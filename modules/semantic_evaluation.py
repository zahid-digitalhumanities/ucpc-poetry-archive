"""
UCPC Semantic Evaluation Module
Research-grade semantic retrieval evaluation
Digital Humanities / Computational Philology
"""

import numpy as np
from statistics import mean


class SemanticEvaluator:
    """
    Evaluate semantic retrieval quality for Urdu poetry embeddings.
    """

    def __init__(self):
        pass

    def precision_at_k(self, relevant, retrieved, k=5):
        retrieved_k = retrieved[:k]
        if not retrieved_k:
            return 0.0
        relevant_found = len(set(relevant).intersection(set(retrieved_k)))
        return round(relevant_found / k, 4)

    def recall_at_k(self, relevant, retrieved, k=5):
        retrieved_k = retrieved[:k]
        if not relevant:
            return 0.0
        relevant_found = len(set(relevant).intersection(set(retrieved_k)))
        return round(relevant_found / len(relevant), 4)

    def reciprocal_rank(self, relevant, retrieved):
        for idx, item in enumerate(retrieved):
            if item in relevant:
                return round(1 / (idx + 1), 4)
        return 0.0

    def mean_reciprocal_rank(self, evaluations):
        scores = [self.reciprocal_rank(ev["relevant"], ev["retrieved"]) for ev in evaluations]
        if not scores:
            return 0.0
        return round(mean(scores), 4)

    def ndcg_at_k(self, relevant, retrieved, k=5):
        retrieved_k = retrieved[:k]
        dcg = 0.0
        for i, item in enumerate(retrieved_k):
            if item in relevant:
                dcg += 1 / np.log2(i + 2)
        ideal_hits = min(len(relevant), k)
        idcg = sum(1 / np.log2(i + 2) for i in range(ideal_hits))
        if idcg == 0:
            return 0.0
        return round(dcg / idcg, 4)

    def evaluate_query(self, relevant, retrieved, k=5):
        return {
            "precision_at_k": self.precision_at_k(relevant, retrieved, k),
            "recall_at_k": self.recall_at_k(relevant, retrieved, k),
            "mrr": self.reciprocal_rank(relevant, retrieved),
            "ndcg_at_k": self.ndcg_at_k(relevant, retrieved, k)
        }

    def corpus_evaluation(self, evaluations, k=5):
        precision_scores = []
        recall_scores = []
        mrr_scores = []
        ndcg_scores = []
        for ev in evaluations:
            metrics = self.evaluate_query(ev["relevant"], ev["retrieved"], k)
            precision_scores.append(metrics["precision_at_k"])
            recall_scores.append(metrics["recall_at_k"])
            mrr_scores.append(metrics["mrr"])
            ndcg_scores.append(metrics["ndcg_at_k"])
        return {
            "queries_evaluated": len(evaluations),
            "mean_precision_at_k": round(mean(precision_scores), 4) if precision_scores else 0,
            "mean_recall_at_k": round(mean(recall_scores), 4) if recall_scores else 0,
            "mean_mrr": round(mean(mrr_scores), 4) if mrr_scores else 0,
            "mean_ndcg_at_k": round(mean(ndcg_scores), 4) if ndcg_scores else 0
        }

    def interpret_results(self, metrics):
        precision = metrics.get("mean_precision_at_k", 0)
        ndcg = metrics.get("mean_ndcg_at_k", 0)
        interpretation = []
        if precision >= 0.8:
            interpretation.append("High semantic retrieval precision.")
        elif precision >= 0.6:
            interpretation.append("Moderate semantic retrieval precision.")
        else:
            interpretation.append("Low semantic retrieval precision.")
        if ndcg >= 0.8:
            interpretation.append("Ranking quality is research-grade.")
        elif ndcg >= 0.6:
            interpretation.append("Ranking quality is acceptable.")
        else:
            interpretation.append("Ranking quality requires improvement.")
        return interpretation


if __name__ == "__main__":
    evaluator = SemanticEvaluator()
    relevant = [1, 2, 3]
    retrieved = [2, 7, 1, 5, 3]
    metrics = evaluator.evaluate_query(relevant, retrieved, k=5)
    print("\nUCPC Semantic Evaluation")
    print("=" * 50)
    for key, value in metrics.items():
        print(f"{key}: {value}")