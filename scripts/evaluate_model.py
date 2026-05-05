# scripts/evaluate_model.py
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
from models.base import get_db_connection

def hash_str(s, n_bins=100):
    if not s:
        return 0
    return hash(s) % n_bins

def main():
    conn = get_db_connection()
    cur = conn.cursor()
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
        print("❌ No data found.")
        return

    X = []
    y = []
    for row in rows:
        poet_id = row['poet_id']
        radif = row['radif'] or ''
        qaafiya_list = row['qaafiya'] or []
        meter = row['meter'] or ''
        theme = row['theme'] or ''
        emb = row['embedding_vector']
        if isinstance(emb, str):
            try:
                emb = json.loads(emb)
            except:
                emb = None
        if emb is None:
            emb = [0.0] * 384
        elif len(emb) != 384:
            emb = list(emb) + [0.0] * (384 - len(emb))

        features = list(emb)
        features.append(hash_str(radif, 100))
        q_hashes = [hash_str(w, 100) for w in qaafiya_list[:3]]
        while len(q_hashes) < 3:
            q_hashes.append(0)
        features.extend(q_hashes)
        features.append(hash_str(meter, 50))
        features.append(hash_str(theme, 10))
        features.append(len(qaafiya_list))

        X.append(features)
        y.append(poet_id)

    # Encode labels
    le = LabelEncoder()
    y_encoded = le.fit_transform(y)

    # Train-test split (80-20)
    X_train, X_test, y_train, y_test = train_test_split(X, y_encoded, test_size=0.2, random_state=42, stratify=y_encoded)

    # Train classifier
    clf = RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1)
    clf.fit(X_train, y_train)

    # Predict
    y_pred = clf.predict(X_test)
    y_proba = clf.predict_proba(X_test)

    # Top-1 accuracy
    acc_top1 = accuracy_score(y_test, y_pred)
    print(f"✅ Top-1 Accuracy: {acc_top1:.3f} ({acc_top1*100:.1f}%)")

    # Top-3 accuracy
    top3_correct = 0
    for i, true in enumerate(y_test):
        top3_idx = y_proba[i].argsort()[-3:][::-1]
        if true in top3_idx:
            top3_correct += 1
    acc_top3 = top3_correct / len(y_test)
    print(f"✅ Top-3 Accuracy: {acc_top3:.3f} ({acc_top3*100:.1f}%)")

    # Per-class report (map back to poet names)
    poet_names = {i: le.inverse_transform([i])[0] for i in range(len(le.classes_))}
    print("\n📊 Classification Report (by poet ID):")
    print(classification_report(y_test, y_pred, target_names=[str(poet_names[i]) for i in sorted(set(y_test))]))

    # Show worst-predicted poets
    from collections import Counter
    errors = [poet_names[y_test[i]] for i in range(len(y_test)) if y_pred[i] != y_test[i]]
    if errors:
        print("\n⚠️ Poets with most misclassifications:")
        for poet, count in Counter(errors).most_common(5):
            print(f"   {poet}: {count} errors")

if __name__ == "__main__":
    main()