# models/ml/train_poet_classifier_v7.py
import os
import pandas as pd
import pickle

from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import classification_report
from xgboost import XGBClassifier

# ================= PATHS =================
BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_PATH = os.path.join(BASE, "scripts", "training_data.csv")   # adjust if needed
SAVE_PATH = os.path.join(BASE, "models", "ml", "poet_classifier_v7.pkl")

print("🚀 Training model...")

df = pd.read_csv(DATA_PATH).dropna()
X = df['text_urdu']
y = df['poet_id']

le = LabelEncoder()
y_enc = le.fit_transform(y)

X_train, X_test, y_train, y_test = train_test_split(X, y_enc, test_size=0.2, random_state=42, stratify=y_enc)

pipeline = Pipeline([
    ("tfidf", TfidfVectorizer(max_features=5384, ngram_range=(1,2), analyzer='char_wb')),
    ("clf", XGBClassifier(n_estimators=200, max_depth=6, learning_rate=0.1, eval_metric='mlogloss', use_label_encoder=False))
])

pipeline.fit(X_train, y_train)
y_pred = pipeline.predict(X_test)

print("\n📊 Classification Report:\n")
print(classification_report(y_test, y_pred))

with open(SAVE_PATH, "wb") as f:
    pickle.dump({"pipeline": pipeline, "label_encoder": le}, f)

print(f"\n✅ Model saved at: {SAVE_PATH}")