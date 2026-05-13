"""
Research-grade confusion analysis for UCPC
Digital Humanities authorship attribution evaluation
"""

from collections import defaultdict
import numpy as np


class ConfusionAnalyzer:
    """
    Analyze poet prediction confusions.
    """

    def __init__(self, label_encoder=None, poet_info=None):
        self.label_encoder = label_encoder
        self.poet_info = poet_info or {}

    def decode_label(self, encoded_label):
        try:
            poet_id = int(self.label_encoder.inverse_transform([encoded_label])[0])
            poet_data = self.poet_info.get(poet_id, {})
            return {
                "poet_id": poet_id,
                "name": poet_data.get("name", f"Poet_{poet_id}"),
                "name_urdu": poet_data.get("name_urdu", "")
            }
        except Exception:
            return {
                "poet_id": encoded_label,
                "name": str(encoded_label),
                "name_urdu": ""
            }

    def analyze_major_confusions(self, y_true, y_pred, top_n=20):
        confusion_counts = defaultdict(int)
        for true_label, pred_label in zip(y_true, y_pred):
            if true_label != pred_label:
                confusion_counts[(true_label, pred_label)] += 1
        sorted_confusions = sorted(confusion_counts.items(), key=lambda x: x[1], reverse=True)
        results = []
        for (true_label, pred_label), count in sorted_confusions[:top_n]:
            true_poet = self.decode_label(true_label)
            pred_poet = self.decode_label(pred_label)
            results.append({
                "true_poet": true_poet,
                "predicted_poet": pred_poet,
                "count": count
            })
        return results

    def poet_level_accuracy(self, y_true, y_pred):
        poet_stats = defaultdict(lambda: {"correct": 0, "total": 0})
        for true_label, pred_label in zip(y_true, y_pred):
            poet_stats[true_label]["total"] += 1
            if true_label == pred_label:
                poet_stats[true_label]["correct"] += 1
        results = []
        for label, stats in poet_stats.items():
            poet = self.decode_label(label)
            accuracy = stats["correct"] / stats["total"] if stats["total"] > 0 else 0
            results.append({
                "poet_id": poet["poet_id"],
                "poet_name": poet["name"],
                "poet_name_urdu": poet["name_urdu"],
                "accuracy": round(accuracy, 4),
                "correct_predictions": stats["correct"],
                "total_samples": stats["total"]
            })
        results = sorted(results, key=lambda x: x["accuracy"], reverse=True)
        return results

    def confusion_clusters(self, y_true, y_pred):
        clusters = defaultdict(set)
        for true_label, pred_label in zip(y_true, y_pred):
            if true_label != pred_label:
                true_poet = self.decode_label(true_label)["name"]
                pred_poet = self.decode_label(pred_label)["name"]
                clusters[true_poet].add(pred_poet)
        results = []
        for poet, confused_with in clusters.items():
            results.append({
                "poet": poet,
                "confused_with": list(confused_with),
                "cluster_size": len(confused_with)
            })
        results = sorted(results, key=lambda x: x["cluster_size"], reverse=True)
        return results

    def research_summary(self, y_true, y_pred):
        total = len(y_true)
        correct = np.sum(np.array(y_true) == np.array(y_pred))
        accuracy = correct / total if total else 0
        major_confusions = self.analyze_major_confusions(y_true, y_pred, top_n=10)
        return {
            "total_samples": total,
            "correct_predictions": int(correct),
            "incorrect_predictions": int(total - correct),
            "overall_accuracy": round(accuracy, 4),
            "major_confusions": major_confusions
        }


if __name__ == "__main__":
    y_true = [0, 1, 2, 0, 1, 2, 0, 1]
    y_pred = [0, 1, 1, 0, 2, 2, 1, 1]
    analyzer = ConfusionAnalyzer()
    summary = analyzer.research_summary(y_true, y_pred)
    print("\nUCPC Confusion Analysis")
    print("=" * 50)
    print(f"Accuracy: {summary['overall_accuracy']}")
    print("\nMajor Confusions:")
    for item in summary["major_confusions"]:
        print(f"{item['true_poet']['name']} → {item['predicted_poet']['name']} ({item['count']})")