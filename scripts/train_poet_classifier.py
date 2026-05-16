# scripts/train_poet_classifier.py
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pickle
import json
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
from models.base import get_db_connection

def hash_str(s, n_bins=100):
    """Simple hash of a string into a fixed number of bins."""
    if not s:
        return 0
    return hash(s) % n_bins

def main():
    conn = get_db_connection()
    cur = conn.cursor()

    # Fetch all ghazals with poet_id and features
    cur.execute("""
        SELECT t.id, t.poet_id,
               pf.radif, pf.qaafiya, pf.meter, pf.theme,
               g.embedding_vector
        FROM texts t
        LEFT JOIN poetic_features pf ON t.id = pf.text_id
        LEFT JOIN ghazal_embeddings g ON t.id = g.text_id
        WHERE t.poet_id IS NOT NULL
    """)
    rows = cur.fetchall()
    cur.close()
    conn.close()

    if not rows:
        print("❌ No data found. Run embedding generation first.")
        return

    X = []   # feature vectors
    y = []   # poet ids

    for row in rows:
        poet_id = row['poet_id']
        radif = row['radif'] or ''
        qaafiya_list = row['qaafiya'] or []
        meter = row['meter'] or ''
        theme = row['theme'] or ''
        emb = row['embedding_vector']
        if isinstance(emb, str):
            emb = json.loads(emb)
        if emb is None:
            # Fallback: zero vector of dimension 384 (MiniLM size)
            emb = [0.0] * 384

        # Build feature vector: embedding + hashed categorical features
        features = list(emb)
        features.append(hash_str(radif, 100))
        # Qaafiya: first 3 words hashed
        q_hashes = [hash_str(w, 100) for w in qaafiya_list[:3]]
        while len(q_hashes) < 3:
            q_hashes.append(0)
        features.extend(q_hashes)
        features.append(hash_str(meter, 50))
        features.append(hash_str(theme, 10))
        features.append(len(qaafiya_list))   # number of qaafiya words
        X.append(features)
        y.append(poet_id)

    # Encode poet labels
    le = LabelEncoder()
    y_encoded = le.fit_transform(y)

    # Train Random Forest
    clf = RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1)
    clf.fit(X, y_encoded)

    # Save model and label encoder
    os.makedirs('models', exist_ok=True)
    model_path = os.path.join('models', 'poet_classifier.pkl')
    with open(model_path, 'wb') as f:
        pickle.dump((clf, le), f)
    print(f"✅ Model trained on {len(X)} ghazals. Saved to {model_path}")

if __name__ == "__main__":
    main()