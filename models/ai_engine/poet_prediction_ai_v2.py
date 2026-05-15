# ============================================
# UCPC Lightweight Poet Prediction
# ============================================

import joblib
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MODEL_PATH = os.path.join(BASE_DIR, "models", "ml", "poet_classifier_v9.pkl")
VECTORIZER_PATH = os.path.join(BASE_DIR, "models", "ml", "tfidf_vectorizer_v9.pkl")

model = None
vectorizer = None

def load_models():
    global model, vectorizer
    if model is None:
        print("🧠 Loading poet classifier...")
        model = joblib.load(MODEL_PATH)
    if vectorizer is None:
        print("📚 Loading TF-IDF vectorizer...")
        vectorizer = joblib.load(VECTORIZER_PATH)

def predict_poet(text, top_k=5):
    try:
        load_models()
        X = vectorizer.transform([text])
        probs = model.predict_proba(X)[0]
        classes = model.classes_
        pairs = sorted(zip(classes, probs), key=lambda x: x[1], reverse=True)
        results = [{"poet_name": poet, "confidence": float(score)} for poet, score in pairs[:top_k]]
        return results
    except Exception as e:
        return [{"poet_name": "Error", "confidence": 0, "error": str(e)}]

# ========== WRAPPER FOR ROUTES (CRITICAL) ==========
def predict_poet_from_text(text, top_n=5):
    """Routes ke liye wrapper function."""
    return predict_poet(text, top_k=top_n)

def get_model_info():
    """Model info for routes/research_validation_routes.py"""
    try:
        load_models()
        return {
            "loaded": True,
            "accuracy": "75.6%",
            "num_poets": 27,
            "version": "v9-lightweight"
        }
    except Exception as e:
        return {"loaded": False, "error": str(e)}

def predict_batch(texts, top_n=3):
    """Batch prediction"""
    results = []
    for text in texts:
        results.append(predict_poet_from_text(text, top_n=top_n))
    return results
