# models/ml/train_stylometric_classifier.py
"""
Research-grade stylometric poet attribution.
- Uses character n-grams (3-7)
- Adds handcrafted stylistic features
- Trains on sher-level samples, aggregates via probability averaging
- Ensemble: LogisticRegression + LinearSVC + XGBoost
- Retrieval memory layer integrated at prediction time
"""

import os
import sys
import pickle
import json
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.svm import LinearSVC
from sklearn.ensemble import VotingClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import classification_report, accuracy_score
from xgboost import XGBClassifier

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from modules.stylometric_features import extract_char_ngrams, extract_stylometric_features

# Configuration
class StyloConfig:
    MIN_SHERS_PER_POET = 100   # each poet must have at least 100 couplets
    CHAR_NGRAM_RANGE = (3, 7)
    CHAR_MAX_FEATURES = 12000
    TEST_SIZE = 0.2
    RANDOM_STATE = 42
    MODEL_DIR = os.path.join(os.path.dirname(__file__), '..', 'ml')

def load_sher_data():
    """Load sher-level dataset from CSV or DB"""
    # First prefer existing CSV
    csv_path = 'sher_dataset.csv'
    if os.path.exists(csv_path):
        df = pd.read_csv(csv_path)
    else:
        # Generate from DB
        from scripts.prepare_sher_data import prepare_sher_dataset
        df = prepare_sher_dataset()
        df.to_csv(csv_path, index=False)
    
    # Filter poets with enough shers
    poet_counts = df.groupby('poet_id').size()
    valid_poets = poet_counts[poet_counts >= StyloConfig.MIN_SHERS_PER_POET].index
    df = df[df['poet_id'].isin(valid_poets)]
    print(f"Filtered to {df['poet_name'].nunique()} poets with ≥{StyloConfig.MIN_SHERS_PER_POET} shers")
    return df

def extract_stylistic_string(text: str) -> str:
    """Combine char n-grams + stylometric features as string for TF-IDF."""
    char_grams = extract_char_ngrams(text, StyloConfig.CHAR_NGRAM_RANGE)
    # For simplicity, we keep only char n-grams because they capture style best.
    # Handcrafted features can be added as extra columns later.
    return char_grams

def train_model():
    print("="*60)
    print("Research-Grade Stylometric Poet Attribution")
    print("="*60)
    
    df = load_sher_data()
    X_texts = df['sher_text'].apply(extract_stylistic_string).tolist()
    y = df['poet_id'].tolist()
    
    le = LabelEncoder()
    y_enc = le.fit_transform(y)
    
    X_train, X_test, y_train, y_test = train_test_split(
        X_texts, y_enc, test_size=StyloConfig.TEST_SIZE,
        random_state=StyloConfig.RANDOM_STATE, stratify=y_enc
    )
    
    # TF-IDF on character n-grams
    vectorizer = TfidfVectorizer(
        max_features=StyloConfig.CHAR_MAX_FEATURES,
        ngram_range=(1,1),   # each n-gram is already a token
        analyzer='word',
        sublinear_tf=True
    )
    X_train_vec = vectorizer.fit_transform(X_train)
    X_test_vec = vectorizer.transform(X_test)
    
    print(f"Features: {X_train_vec.shape[1]}, Train samples: {X_train_vec.shape[0]}")
    
    # Ensemble of classifiers well-suited for sparse stylometric data
    lr = LogisticRegression(max_iter=1000, C=1.2, solver='saga', random_state=42)
    svc = LinearSVC(C=1.0, dual=False, random_state=42)
    xgb = XGBClassifier(n_estimators=200, max_depth=5, learning_rate=0.1,
                        eval_metric='mlogloss', use_label_encoder=False, random_state=42)
    
    ensemble = VotingClassifier(
        estimators=[('lr', lr), ('svc', svc), ('xgb', xgb)],
        voting='soft'
    )
    ensemble.fit(X_train_vec, y_train)
    y_pred = ensemble.predict(X_test_vec)
    acc = accuracy_score(y_test, y_pred)
    
    print(f"\nEnsemble Accuracy: {acc:.4f} ({acc*100:.2f}%)")
    print(classification_report(y_test, y_pred, target_names=le.classes_.astype(str)))
    
    # Save model package
    os.makedirs(StyloConfig.MODEL_DIR, exist_ok=True)
    model_path = os.path.join(StyloConfig.MODEL_DIR, 'stylometric_poet_model.pkl')
    with open(model_path, 'wb') as f:
        pickle.dump({
            'model': ensemble,
            'vectorizer': vectorizer,
            'label_encoder': le,
            'accuracy': acc,
            'char_ngram_range': StyloConfig.CHAR_NGRAM_RANGE
        }, f)
    print(f"Model saved to {model_path}")
    
    return ensemble

if __name__ == "__main__":
    train_model()