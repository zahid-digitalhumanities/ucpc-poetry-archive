# models/ml/train_poet_classifier_v8.py
"""
Advanced Poet Classifier Training Script - FULLY FIXED
Works with both tuple and dictionary cursors
"""

import os
import sys
import pickle
import json
import warnings
from datetime import datetime
from typing import Tuple, Dict, List, Any

import numpy as np
from scipy.sparse import hstack, csr_matrix

from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import classification_report, accuracy_score
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, VotingClassifier
from xgboost import XGBClassifier

warnings.filterwarnings('ignore')

# Add project root
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(BASE_DIR)

# Database connection
try:
    from models.base import get_db_connection
except ImportError:
    import psycopg2
    from psycopg2.extras import RealDictCursor
    
    def get_db_connection():
        return psycopg2.connect(
            database="ucpc_v3_db",
            user="postgres",
            password="postgres",
            host="localhost",
            port="5432"
        )

class Config:
    MIN_SAMPLES_PER_POET = 20
    TEST_SIZE = 0.2
    RANDOM_STATE = 42
    CHAR_NGRAM_RANGE = (2, 6)
    CHAR_MAX_FEATURES = 8000
    WORD_NGRAM_RANGE = (1, 2)
    WORD_MAX_FEATURES = 5000
    MODEL_DIR = os.path.join(BASE_DIR, "models", "ml")
    
    XGB_PARAMS = {
        'n_estimators': 200,
        'max_depth': 6,
        'learning_rate': 0.1,
        'subsample': 0.8,
        'colsample_bytree': 0.8,
        'eval_metric': 'mlogloss',
        'use_label_encoder': False,
        'random_state': 42
    }
    
    RF_PARAMS = {
        'n_estimators': 150,
        'max_depth': 12,
        'min_samples_split': 5,
        'random_state': 42,
        'n_jobs': -1
    }
    
    LR_PARAMS = {
        'max_iter': 1000,
        'C': 1.0,
        'solver': 'lbfgs',
        'random_state': 42
    }

def load_from_db(min_samples: int = 20):
    """Load training data - FIXED VERSION"""
    conn = get_db_connection()
    
    # Try dictionary cursor first
    try:
        cur = conn.cursor()
    except:
        cur = conn.cursor()
    
    # Get poets with sufficient ghazals
    cur.execute("""
        SELECT 
            p.id, 
            p.name, 
            p.name_urdu,
            COUNT(t.id) as ghazal_count
        FROM poets p
        JOIN texts t ON p.id = t.poet_id
        WHERE t.form = 'ghazal'
          AND (t.is_deleted = FALSE OR t.is_deleted IS NULL)
          AND t.integrity_status IN ('clean', 'merged')
          AND t.text_urdu IS NOT NULL
          AND LENGTH(t.text_urdu) > 100
        GROUP BY p.id, p.name, p.name_urdu
        HAVING COUNT(t.id) >= %s
        ORDER BY p.name
    """, (min_samples,))
    
    poets = cur.fetchall()
    print(f"📊 Found {len(poets)} poets with ≥{min_samples} ghazals")
    
    if len(poets) < 2:
        cur.close()
        conn.close()
        raise ValueError(f"Need at least 2 poets, found {len(poets)}")
    
    all_ghazals = []
    all_labels = []
    poet_info = {}
    
    for poet in poets:
        # Handle both tuple and dict results
        if isinstance(poet, dict):
            poet_id = poet['id']
            poet_name = poet['name']
            poet_name_urdu = poet['name_urdu']
            poet_count = poet['ghazal_count']
        else:
            poet_id = poet[0]
            poet_name = poet[1]
            poet_name_urdu = poet[2]
            poet_count = poet[3] if len(poet) > 3 else 0
        
        poet_info[poet_id] = {
            'name': poet_name,
            'name_urdu': poet_name_urdu
        }
        
        # Get ghazals for this poet
        cur.execute("""
            SELECT text_urdu, normalized_text
            FROM texts
            WHERE poet_id = %s
              AND form = 'ghazal'
              AND (is_deleted = FALSE OR is_deleted IS NULL)
              AND integrity_status IN ('clean', 'merged')
              AND text_urdu IS NOT NULL
              AND LENGTH(text_urdu) > 100
            ORDER BY id
        """, (poet_id,))
        
        ghazals = cur.fetchall()
        
        for g in ghazals:
            if isinstance(g, dict):
                text = g['normalized_text'] or g['text_urdu']
            else:
                text = g[1] if g[1] else g[0]
            
            text = ' '.join(text.split())
            if len(text) > 50:
                all_ghazals.append(text)
                all_labels.append(poet_id)
        
        print(f"  ✓ {poet_name}: {len(ghazals)} ghazals")
    
    cur.close()
    conn.close()
    
    print(f"\n📈 Total training samples: {len(all_ghazals)}")
    return all_ghazals, all_labels, poet_info

class AdvancedTextVectorizer:
    def __init__(self):
        self.char_vectorizer = TfidfVectorizer(
            max_features=8000,
            ngram_range=(2, 6),
            analyzer='char_wb',
            sublinear_tf=True
        )
        self.word_vectorizer = TfidfVectorizer(
            max_features=5000,
            ngram_range=(1, 2),
            analyzer='word',
            sublinear_tf=True,
            min_df=2,
            max_df=0.95
        )
        self.fitted = False
    
    def fit(self, texts):
        print("  Fitting character-level TF-IDF...")
        self.char_vectorizer.fit(texts)
        print("  Fitting word-level TF-IDF...")
        self.word_vectorizer.fit(texts)
        self.fitted = True
        return self
    
    def transform(self, texts):
        if not self.fitted:
            raise ValueError("Must fit first")
        char_features = self.char_vectorizer.transform(texts)
        word_features = self.word_vectorizer.transform(texts)
        return hstack([char_features, word_features])
    
    def fit_transform(self, texts):
        self.fit(texts)
        return self.transform(texts)

def train_model():
    """Main training function"""
    print("="*70)
    print("🚀 POET CLASSIFIER TRAINING v8 (FULLY FIXED)")
    print("="*70)
    
    # Load data
    print("\n📂 Loading training data...")
    X_texts, y_labels, poet_info = load_from_db(Config.MIN_SAMPLES_PER_POET)
    
    if len(X_texts) < 100:
        print(f"❌ Not enough data: {len(X_texts)} samples")
        return None
    
    # Encode labels
    le = LabelEncoder()
    y_encoded = le.fit_transform(y_labels)
    
    print(f"\n🎯 Training on {len(le.classes_)} poets:")
    for i, poet_id in enumerate(le.classes_):
        poet_name = poet_info.get(poet_id, {}).get('name', f"Poet_{poet_id}")
        count = list(y_labels).count(poet_id)
        print(f"  {i}: {poet_name} - {count} samples")
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X_texts, y_encoded,
        test_size=Config.TEST_SIZE,
        random_state=Config.RANDOM_STATE,
        stratify=y_encoded
    )
    
    # Extract features
    print("\n🔧 Extracting features...")
    vectorizer = AdvancedTextVectorizer()
    X_train_features = vectorizer.fit_transform(X_train)
    X_test_features = vectorizer.transform(X_test)
    
    print(f"  Features: {X_train_features.shape[1]:,}")
    print(f"  Train samples: {X_train_features.shape[0]}")
    print(f"  Test samples: {X_test_features.shape[0]}")
    
    # Train models
    print("\n📊 Training models...")
    models = {}
    
    # XGBoost
    print("\n  Training XGBoost...")
    xgb = XGBClassifier(**Config.XGB_PARAMS)
    xgb.fit(X_train_features, y_train)
    xgb_acc = accuracy_score(y_test, xgb.predict(X_test_features))
    print(f"    XGBoost Accuracy: {xgb_acc:.4f}")
    models['xgb'] = xgb
    
    # Random Forest
    print("\n  Training Random Forest...")
    rf = RandomForestClassifier(**Config.RF_PARAMS)
    rf.fit(X_train_features, y_train)
    rf_acc = accuracy_score(y_test, rf.predict(X_test_features))
    print(f"    Random Forest Accuracy: {rf_acc:.4f}")
    models['rf'] = rf
    
    # Logistic Regression
    print("\n  Training Logistic Regression...")
    lr = LogisticRegression(**Config.LR_PARAMS)
    lr.fit(X_train_features, y_train)
    lr_acc = accuracy_score(y_test, lr.predict(X_test_features))
    print(f"    Logistic Regression Accuracy: {lr_acc:.4f}")
    models['lr'] = lr
    
    # Find best individual model
    best_model_name = max(models.keys(), key=lambda x: accuracy_score(y_test, models[x].predict(X_test_features)))
    best_model = models[best_model_name]
    best_accuracy = accuracy_score(y_test, best_model.predict(X_test_features))
    
    # Create ensemble
    print("\n  Creating Ensemble...")
    try:
        ensemble = VotingClassifier(
            estimators=[(name, model) for name, model in models.items()],
            voting='soft'
        )
        ensemble.fit(X_train_features, y_train)
        ensemble_acc = accuracy_score(y_test, ensemble.predict(X_test_features))
        print(f"    Ensemble Accuracy: {ensemble_acc:.4f}")
        
        if ensemble_acc > best_accuracy:
            best_model = ensemble
            best_accuracy = ensemble_acc
            best_model_name = 'ensemble'
    except Exception as e:
        print(f"    Ensemble failed: {e}")
    
    # Print detailed report
    print("\n" + "="*70)
    print("📊 FINAL REPORT")
    print("="*70)
    y_pred = best_model.predict(X_test_features)
    
    # Get poet names for display
    target_names = [poet_info.get(pid, {}).get('name', f"Poet_{pid}") for pid in le.classes_]
    
    print(classification_report(y_test, y_pred, target_names=target_names))
    print(f"\n🎯 Best Model: {best_model_name.upper()}")
    print(f"🎯 Accuracy: {best_accuracy:.4f} ({best_accuracy*100:.2f}%)")
    
    # Save model
    os.makedirs(Config.MODEL_DIR, exist_ok=True)
    model_path = os.path.join(Config.MODEL_DIR, 'poet_classifier_v8.pkl')
    
    model_package = {
        'model': best_model,
        'vectorizer': vectorizer,
        'label_encoder': le,
        'poet_info': poet_info,
        'accuracy': best_accuracy,
        'training_date': datetime.now().isoformat(),
        'num_poets': len(le.classes_),
        'total_samples': len(X_texts)
    }
    
    with open(model_path, 'wb') as f:
        pickle.dump(model_package, f)
    
    print(f"\n✅ Model saved to: {model_path}")
    
    return model_package

if __name__ == "__main__":
    train_model()