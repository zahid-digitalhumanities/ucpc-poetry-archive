# scripts/compute_model_metrics.py
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
from models.base import get_db_connection
from modules.poet_classifier import hash_str

def compute_metrics():
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
        print("No data found")
        return

    X, y = [], []
    poet_ids = []
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
        poet_ids.append(poet_id)

    le = LabelEncoder()
    y_encoded = le.fit_transform(y)

    # Train-test split (80-20)
    X_train, X_test, y_train, y_test = train_test_split(X, y_encoded, test_size=0.2, random_state=42, stratify=y_encoded)

    clf = RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1)
    clf.fit(X_train, y_train)
    y_pred = clf.predict(X_test)

    # Metrics
    acc_top1 = accuracy_score(y_test, y_pred)
    y_proba = clf.predict_proba(X_test)
    top3_correct = 0
    for i, true in enumerate(y_test):
        top3_idx = y_proba[i].argsort()[-3:][::-1]
        if true in top3_idx:
            top3_correct += 1
    acc_top3 = top3_correct / len(y_test)

    # Classification report
    target_names = [str(le.inverse_transform([i])[0]) for i in range(len(le.classes_))]
    report = classification_report(y_test, y_pred, target_names=target_names, output_dict=True, zero_division=0)

    # Confusion matrix
    cm = confusion_matrix(y_test, y_pred).tolist()
    # Convert to Python ints
    cm = [[int(cell) for cell in row] for row in cm]

    # Poet labels as Python ints
    poet_labels = [int(le.inverse_transform([i])[0]) for i in range(len(le.classes_))]

    # Poet name mapping (id -> name)
    poet_name_map = {}
    for pid in set(poet_ids):
        conn2 = get_db_connection()
        cur2 = conn2.cursor()
        cur2.execute("SELECT name, name_urdu FROM poets WHERE id = %s", (pid,))
        row2 = cur2.fetchone()
        if row2:
            poet_name_map[pid] = {'name': row2['name'], 'name_urdu': row2['name_urdu']}
        cur2.close()
        conn2.close()

    # Prepare per-poet metrics with native types
    per_poet = []
    for poet_id in poet_labels:
        pid = int(poet_id)
        info = poet_name_map.get(pid, {'name': f"Poet {pid}", 'name_urdu': ''})
        metrics = report.get(str(pid), {})
        per_poet.append({
            'poet_id': pid,
            'name': str(info['name']),
            'name_urdu': str(info.get('name_urdu', '')),
            'precision': float(metrics.get('precision', 0)),
            'recall': float(metrics.get('recall', 0)),
            'f1': float(metrics.get('f1-score', 0)),
            'support': int(metrics.get('support', 0))
        })

    # Save to JSON file
    output = {
        'top1_accuracy': float(acc_top1),
        'top3_accuracy': float(acc_top3),
        'total_ghazals': int(len(y)),
        'test_ghazals': int(len(y_test)),
        'confusion_matrix': cm,
        'poet_labels': poet_labels,
        'per_poet': per_poet
    }
    os.makedirs('data', exist_ok=True)
    with open('data/model_metrics.json', 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2)

    print(f"✅ Metrics saved to data/model_metrics.json")
    print(f"Top-1 Accuracy: {acc_top1:.3f}")
    print(f"Top-3 Accuracy: {acc_top3:.3f}")

if __name__ == "__main__":
    compute_metrics()