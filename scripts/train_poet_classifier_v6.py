import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
import pickle
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score, top_k_accuracy_score
from sklearn.preprocessing import LabelEncoder
from sklearn.feature_extraction.text import TfidfVectorizer
import xgboost as xgb
from models.base import get_db_connection

def main():
    conn = get_db_connection()
    cur = conn.cursor()

    print("🔄 Loading dataset...")
    cur.execute("""
        SELECT 
            t.id,
            t.text_urdu,
            t.poet_id,
            g.embedding_vector
        FROM texts t
        LEFT JOIN ghazal_embeddings g ON t.id = g.text_id
        WHERE t.poet_id IS NOT NULL
          AND t.text_urdu IS NOT NULL
          AND t.text_urdu != ''
    """)
    rows = cur.fetchall()
    cur.close()
    conn.close()

    print(f"📊 Rows fetched: {len(rows)}")

    texts = []
    embeddings = []
    labels = []

    for row in rows:
        text = row['text_urdu'] or ""
        poet_id = row['poet_id']
        emb = row['embedding_vector']

        if isinstance(emb, str):
            try:
                emb = json.loads(emb)
            except:
                emb = None

        if emb is None or len(emb) != 384:
            emb = [0.0] * 384

        texts.append(text)
        embeddings.append(emb)
        labels.append(poet_id)

    # Filter poets with at least 30 ghazals (optional, for stability)
    from collections import Counter
    poet_counts = Counter(labels)
    min_samples = 30
    valid_poets = {p for p, c in poet_counts.items() if c >= min_samples}
    filtered_indices = [i for i, p in enumerate(labels) if p in valid_poets]
    texts = [texts[i] for i in filtered_indices]
    embeddings = [embeddings[i] for i in filtered_indices]
    labels = [labels[i] for i in filtered_indices]
    print(f"✅ After filtering (≥{min_samples} per poet): {len(texts)} samples")

    print("🧠 Building character n‑gram features (3–5)...")
    vectorizer = TfidfVectorizer(
        analyzer='char',
        ngram_range=(3, 5),
        max_features=5000,
        min_df=2,
        max_df=0.8
    )
    X_ngram = vectorizer.fit_transform(texts)
    print(f"   N‑gram matrix shape: {X_ngram.shape}")

    print("🔗 Combining embeddings (384) + n‑grams (5000)...")
    X_emb = np.array(embeddings)
    X = np.hstack([X_emb, X_ngram.toarray()])
    print(f"   Final feature dimension: {X.shape[1]}")

    le = LabelEncoder()
    y = le.fit_transform(labels)

    # Stratified split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    print("🚀 Training XGBoost (with sample weights for imbalance)...")
    # Compute sample weights (inverse class frequency)
    from collections import Counter
    class_counts = Counter(y_train)
    n_train = len(y_train)
    n_classes = len(class_counts)
    sample_weights = np.array([n_train / (n_classes * class_counts[cls]) for cls in y_train])

    model = xgb.XGBClassifier(
        n_estimators=300,
        max_depth=6,
        learning_rate=0.1,
        subsample=0.8,
        colsample_bytree=0.8,
        eval_metric='mlogloss',
        n_jobs=-1,
        random_state=42
    )
    model.fit(X_train, y_train, sample_weight=sample_weights)

    print("📊 Evaluating...")
    y_pred = model.predict(X_test)
    y_proba = model.predict_proba(X_test)

    acc = accuracy_score(y_test, y_pred)
    top3_acc = top_k_accuracy_score(y_test, y_proba, k=3, labels=model.classes_)

    print(f"\n📊 Top-1 Accuracy: {acc:.3f}")
    print(f"📊 Top-3 Accuracy: {top3_acc:.3f}")

    print("\n📋 Classification Report:\n")
    target_names = [str(le.inverse_transform([i])[0]) for i in range(len(le.classes_))]
    print(classification_report(y_test, y_pred, target_names=target_names))

    # Save model, label encoder, vectorizer
    os.makedirs("models/ml", exist_ok=True)
    model_path = "models/ml/poet_classifier_v6.pkl"
    with open(model_path, "wb") as f:
        pickle.dump({
            "model": model,
            "label_encoder": le,
            "vectorizer": vectorizer
        }, f)
    print(f"\n💾 Model saved: {model_path}")

if __name__ == "__main__":
    main()