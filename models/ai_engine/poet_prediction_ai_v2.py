# ============================================
# UCPC Lightweight Poet Prediction
# ============================================

import joblib

MODEL_PATH = "models/ml/poet_classifier_v9.pkl"
VECTORIZER_PATH = "models/ml/tfidf_vectorizer_v9.pkl"

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
        return {
            "success": True,
            "method": "TF-IDF + Logistic Regression",
            "data": results
        }
    except Exception as e:
        return {"success": False, "error": str(e)}
