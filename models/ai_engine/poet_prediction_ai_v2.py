# ============================================
# UCPC Lightweight Poet Prediction
# Fully compatible with routes
# ============================================

import joblib
import os
import numpy as np

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MODEL_PATH = os.path.join(BASE_DIR, "models", "ml", "poet_classifier_v9.pkl")
VECTORIZER_PATH = os.path.join(BASE_DIR, "models", "ml", "tfidf_vectorizer_v9.pkl")

model = None
vectorizer = None


def load_models():
    """Load poet classifier and TF-IDF vectorizer"""
    global model, vectorizer
    if model is None:
        print("🧠 Loading poet classifier...")
        try:
            model = joblib.load(MODEL_PATH)
        except Exception as e:
            print(f"⚠️ Could not load model from {MODEL_PATH}: {e}")
            model = None
    if vectorizer is None:
        print("📚 Loading TF-IDF vectorizer...")
        try:
            vectorizer = joblib.load(VECTORIZER_PATH)
        except Exception as e:
            print(f"⚠️ Could not load vectorizer from {VECTORIZER_PATH}: {e}")
            vectorizer = None


def predict_poet(text, top_k=5):
    """Predict poet from text - returns list of predictions"""
    try:
        load_models()
        if model is None or vectorizer is None:
            return [{"poet_name": "Model not loaded", "confidence": 0, "error": "Models not available"}]
        
        X = vectorizer.transform([text])
        probs = model.predict_proba(X)[0]
        classes = model.classes_
        pairs = sorted(zip(classes, probs), key=lambda x: x[1], reverse=True)
        results = [{"poet_name": poet, "confidence": float(score)} for poet, score in pairs[:top_k]]
        return results
    except Exception as e:
        return [{"poet_name": "Error", "confidence": 0, "error": str(e)}]


# ============================================
# ROUTES COMPATIBILITY FUNCTIONS
# ============================================

def predict_poet_from_text(text, top_n=5):
    """
    Main function for routes - matches expected interface.
    Returns list of predictions.
    """
    return predict_poet(text, top_k=top_n)


def get_model_info():
    """
    Model information for research_validation_routes and health checks.
    """
    try:
        load_models()
        return {
            "loaded": model is not None and vectorizer is not None,
            "accuracy": "75.6%",
            "num_poets": 27,
            "version": "v9-lightweight",
            "training_date": "2026-05-10",
            "model_type": "TF-IDF + Logistic Regression",
            "corpus_version": "1.2",
            "top3_accuracy": "88.9%",
            "top5_accuracy": "93.4%"
        }
    except Exception as e:
        return {
            "loaded": False,
            "error": str(e)
        }


def predict_batch(texts, top_n=3):
    """Batch prediction for multiple texts"""
    results = []
    for text in texts:
        results.append(predict_poet_from_text(text, top_n=top_n))
    return results


# ============================================
# TEST
# ============================================
if __name__ == "__main__":
    test_text = "دل ہی تو ہے نہ سنگ و خشت"
    print("Testing poet prediction...")
    results = predict_poet_from_text(test_text, top_n=3)
    for r in results:
        print(f"{r.get('poet_name')}: {r.get('confidence')}")
