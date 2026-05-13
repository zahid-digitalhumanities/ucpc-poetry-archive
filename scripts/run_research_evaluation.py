"""
UCPC Research Evaluation Script
Runs full evaluation pipeline for poet prediction.
"""

import sys
import os
import json
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.base import get_db_connection
from models.ai_engine.poet_prediction_ai_v2 import predict_poet_from_text
from modules.evaluation_metrics import EvaluationMetrics
from modules.confusion_analysis import ConfusionAnalyzer


def load_poet_test_set(limit=100):
    """Load clean ghazals with ground truth poet labels."""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT t.id, t.text_urdu, t.poet_id, p.name
        FROM texts t
        JOIN poets p ON t.poet_id = p.id
        WHERE t.form = 'ghazal'
          AND (t.is_deleted = FALSE OR t.is_deleted IS NULL)
          AND t.integrity_status = 'clean'
          AND LENGTH(t.text_urdu) > 200
        ORDER BY RANDOM()
        LIMIT %s
    """, (limit,))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    test_set = []
    for row in rows:
        if hasattr(row, 'keys'):
            test_set.append({
                'id': row['id'],
                'text': row['text_urdu'],
                'poet_id': row['poet_id'],
                'poet_name': row['name']
            })
        else:
            test_set.append({
                'id': row[0],
                'text': row[1],
                'poet_id': row[2],
                'poet_name': row[3]
            })
    return test_set


def evaluate_poet_model(test_set):
    """Run poet prediction evaluation."""
    y_true = []
    y_pred = []
    for item in test_set:
        text = item['text']
        true_id = item['poet_id']
        predictions = predict_poet_from_text(text, top_n=5)
        if predictions and not predictions[0].get('error'):
            pred_id = predictions[0].get('poet_id', -1)
        else:
            pred_id = -1
        y_true.append(true_id)
        y_pred.append(pred_id)
    evaluator = EvaluationMetrics()
    metrics = evaluator.evaluate_model(y_true, y_pred)
    analyzer = ConfusionAnalyzer()
    confusion_summary = analyzer.research_summary(y_true, y_pred)
    return metrics, confusion_summary


def main():
    print("=" * 60)
    print("UCPC RESEARCH EVALUATION PIPELINE")
    print("=" * 60)
    print("\n📊 Loading test set...")
    test_set = load_poet_test_set(limit=100)
    print(f"   Loaded {len(test_set)} test ghazals")
    print("\n🔬 Evaluating poet prediction model...")
    metrics, confusion = evaluate_poet_model(test_set)
    print("\n📈 POET PREDICTION METRICS")
    print("-" * 40)
    for key, value in metrics.items():
        if isinstance(value, (int, float)):
            print(f"  {key}: {value}")
    print(f"\n  Overall accuracy: {confusion['overall_accuracy']}")
    print(f"  Correct predictions: {confusion['correct_predictions']}/{confusion['total_samples']}")
    os.makedirs('evaluation', exist_ok=True)
    report = {
        "evaluation_date": datetime.now().isoformat(),
        "poet_prediction": metrics,
        "confusion_summary": confusion,
        "test_set_size": len(test_set)
    }
    with open('evaluation/full_evaluation_report.json', 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print("\n✅ Evaluation complete. Report saved to evaluation/full_evaluation_report.json")


if __name__ == "__main__":
    main()