import os
import pickle
import numpy as np

# Go up three levels: from models/ai_engine/ to project root
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MODEL_PATH = os.path.join(BASE_DIR, 'models', 'ml', 'poet_classifier_v7.pkl')

_model = None
_le = None

def load_model():
    global _model, _le
    if _model is not None:
        return _model, _le
    if not os.path.exists(MODEL_PATH):
        raise FileNotFoundError(f"❌ Model not found at {MODEL_PATH}. Train first.")
    with open(MODEL_PATH, "rb") as f:
        data = pickle.load(f)
        _model = data["pipeline"]
        _le = data["label_encoder"]
    print(f"✅ Model loaded from: {MODEL_PATH}")
    return _model, _le

def predict_poet_from_text(text, top_n=3):
    try:
        model, le = load_model()
        probs = model.predict_proba([text])[0]
        top_idx = np.argsort(probs)[::-1][:top_n]
        results = []
        for i in top_idx:
            poet_id = int(le.inverse_transform([i])[0])
            results.append({"poet_id": poet_id, "confidence": round(float(probs[i]), 4)})
        return results
    except Exception as e:
        print(f"❌ Prediction Error: {e}")
        import traceback
        traceback.print_exc()
        return []