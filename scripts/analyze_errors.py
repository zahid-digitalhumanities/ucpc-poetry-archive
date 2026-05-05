# scripts/analyze_errors.py

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from collections import defaultdict, Counter
from models.base import get_db_connection
from models.poet_prediction_model import predict_poet

def analyze_errors():
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT t.id, t.poet_id, p.name
        FROM texts t
        JOIN poets p ON t.poet_id = p.id
        WHERE t.poet_id IS NOT NULL
          AND t.text_urdu IS NOT NULL
    """)

    rows = cur.fetchall()
    cur.close()
    conn.close()

    print(f"🔍 Total samples: {len(rows)}")

    confusion = defaultdict(int)
    per_poet_correct = Counter()
    per_poet_total = Counter()
    hard_errors = []

    for i, row in enumerate(rows):
        text_id = row['id']
        true_poet_id = row['poet_id']
        true_name = row['name']

        pred = predict_poet(text_id, top_n=3)

        if not pred or 'top_prediction' not in pred:
            continue

        top = pred['top_prediction']
        pred_poet_id = top['poet_id']
        pred_name = top['poet_name']
        confidence = top['probability']

        per_poet_total[true_name] += 1

        if pred_poet_id == true_poet_id:
            per_poet_correct[true_name] += 1
        else:
            confusion[(true_name, pred_name)] += 1

            # store hard errors (high confidence but wrong)
            if confidence > 0.7:
                hard_errors.append({
                    "text_id": text_id,
                    "true": true_name,
                    "pred": pred_name,
                    "confidence": round(confidence, 3)
                })

        if (i + 1) % 200 == 0:
            print(f"Processed {i+1}/{len(rows)}")

    # -------------------------
    # 📊 PER-POET ACCURACY
    # -------------------------
    print("\n📊 PER-POET ACCURACY:\n")
    for poet in sorted(per_poet_total.keys()):
        total = per_poet_total[poet]
        correct = per_poet_correct[poet]
        acc = correct / total if total > 0 else 0
        print(f"{poet:30} {correct:4}/{total:4} = {acc:.2%}")

    # -------------------------
    # 🔥 CONFUSION PAIRS
    # -------------------------
    print("\n🔥 TOP CONFUSION PAIRS (true → predicted):\n")
    for (true, pred), count in sorted(confusion.items(), key=lambda x: x[1], reverse=True)[:20]:
        print(f"{true:30} → {pred:30} = {count}")

    # -------------------------
    # ⚠️ HARD ERRORS
    # -------------------------
    print("\n⚠️ HIGH-CONFIDENCE ERRORS (VERY IMPORTANT FOR RESEARCH):\n")
    for e in hard_errors[:20]:
        print(e)

    print(f"\nTotal hard errors: {len(hard_errors)}")


if __name__ == "__main__":
    analyze_errors()