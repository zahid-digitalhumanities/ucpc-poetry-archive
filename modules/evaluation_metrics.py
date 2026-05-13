"""
Research-grade evaluation metrics for UCPC authorship attribution.
Digital Humanities evaluation infrastructure.
"""

import numpy as np
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
    classification_report,
    top_k_accuracy_score
)


class EvaluationMetrics:
    """
    Computes research-grade evaluation metrics.
    """

    def __init__(self):
        pass

    def compute_basic_metrics(self, y_true, y_pred):
        """
        Compute standard classification metrics.
        """
        return {
            "accuracy": round(accuracy_score(y_true, y_pred), 4),
            "precision_macro": round(
                precision_score(y_true, y_pred, average='macro', zero_division=0), 4
            ),
            "recall_macro": round(
                recall_score(y_true, y_pred, average='macro', zero_division=0), 4
            ),
            "f1_macro": round(
                f1_score(y_true, y_pred, average='macro', zero_division=0), 4
            ),
            "precision_weighted": round(
                precision_score(y_true, y_pred, average='weighted', zero_division=0), 4
            ),
            "recall_weighted": round(
                recall_score(y_true, y_pred, average='weighted', zero_division=0), 4
            ),
            "f1_weighted": round(
                f1_score(y_true, y_pred, average='weighted', zero_division=0), 4
            )
        }

    def compute_topk_accuracy(self, y_true, y_prob, k_values=[1, 3, 5]):
        """
        Compute Top-K accuracy.
        Useful for authorship attribution.
        """
        results = {}
        for k in k_values:
            try:
                score = top_k_accuracy_score(y_true, y_prob, k=k)
                results[f"top_{k}_accuracy"] = round(score, 4)
            except Exception:
                results[f"top_{k}_accuracy"] = 0.0
        return results

    def compute_confusion_matrix(self, y_true, y_pred, labels=None):
        """
        Generate confusion matrix.
        """
        cm = confusion_matrix(y_true, y_pred)
        return {
            "matrix": cm.tolist(),
            "labels": labels if labels else []
        }

    def compute_classification_report(self, y_true, y_pred, target_names=None):
        """
        Detailed classification report.
        """
        report = classification_report(
            y_true,
            y_pred,
            target_names=target_names,
            output_dict=True,
            zero_division=0
        )
        return report

    def evaluate_model(
        self,
        y_true,
        y_pred,
        y_prob=None,
        labels=None,
        target_names=None
    ):
        """
        Full research evaluation.
        """
        results = {}
        results.update(self.compute_basic_metrics(y_true, y_pred))
        if y_prob is not None:
            results.update(self.compute_topk_accuracy(y_true, y_prob))
        results["confusion_matrix"] = self.compute_confusion_matrix(y_true, y_pred, labels)
        results["classification_report"] = self.compute_classification_report(y_true, y_pred, target_names)
        return results


def print_research_summary(metrics):
    """
    Print clean research summary.
    """
    print("\n" + "=" * 60)
    print("UCPC RESEARCH EVALUATION SUMMARY")
    print("=" * 60)
    for key, value in metrics.items():
        if isinstance(value, (int, float)):
            print(f"{key:<30}: {value}")
    print("=" * 60)


if __name__ == "__main__":
    y_true = [0, 1, 2, 0, 1, 2]
    y_pred = [0, 1, 1, 0, 2, 2]
    evaluator = EvaluationMetrics()
    metrics = evaluator.evaluate_model(y_true, y_pred)
    print_research_summary(metrics)