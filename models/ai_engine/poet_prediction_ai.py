# models/ai_engine/poet_prediction_ai_v2.py
"""
Poet Prediction - FULLY FIXED VERSION
"""

import os
import sys
import pickle
import re
import numpy as np

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(BASE_DIR)

MODEL_PATH = os.path.join(BASE_DIR, 'models', 'ml', 'poet_classifier_v8.pkl')
_model_cache = None

def clean_text(text):
    if not text:
        return ""
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def load_model():
    global _model_cache
    if _model_cache is not None:
        return _model_cache
    
    if not os.path.exists(MODEL_PATH):
        raise FileNotFoundError(f"Model not found. Run: python models/ml/train_poet_classifier_v8.py")
    
    with open(MODEL_PATH, 'rb') as f:
        _model_cache = pickle.load(f)
    
    print(f"✅ Model loaded (accuracy: {_model_cache.get('accuracy', 'N/A'):.2%})")
    return _model_cache

def get_poet_name(poet_id, poet_info):
    """Get poet name from the stored info"""
    if poet_info and poet_id in poet_info:
        return poet_info[poet_id].get('name', f"Poet_{poet_id}")
    return f"Poet_{poet_id}"

def predict_poet_from_text(text, top_n=3):
    try:
        text = clean_text(text)
        
        if len(text) < 100:
            return [{
                "poet_id": None,
                "poet_name": "Insufficient Text",
                "confidence": 0.0,
                "confidence_percent": 0,
                "error": "Text too short (minimum 100 characters)"
            }]
        
        model_package = load_model()
        model = model_package['model']
        vectorizer = model_package['vectorizer']
        le = model_package['label_encoder']
        poet_info = model_package.get('poet_info', {})
        
        X_input = vectorizer.transform([text])
        
        if hasattr(model, 'predict_proba'):
            probs = model.predict_proba(X_input)[0]
        else:
            pred = model.predict(X_input)[0]
            probs = np.zeros(len(le.classes_))
            probs[pred] = 1.0
        
        top_indices = np.argsort(probs)[::-1][:top_n]
        
        results = []
        for idx in top_indices:
            confidence = float(probs[idx])
            poet_id = int(le.inverse_transform([idx])[0])
            poet_name = get_poet_name(poet_id, poet_info)
            
            results.append({
                "poet_id": poet_id,
                "poet_name": poet_name,
                "confidence": round(confidence, 4),
                "confidence_percent": round(confidence * 100, 1),
                "confidence_level": "high" if confidence > 0.7 else "moderate" if confidence > 0.5 else "low"
            })
        
        return results
    
    except Exception as e:
        print(f"❌ Error: {e}")
        return [{"poet_id": None, "poet_name": "Error", "confidence": 0.0, "error": str(e)}]

# For testing
if __name__ == "__main__":
    test_text = "دل ہی تو ہے نہ سنگ و خشت، درد سے بھر نہ آئے کیوں"
    results = predict_poet_from_text(test_text, top_n=3)
    for r in results:
        print(f"{r['poet_name']}: {r['confidence_percent']}%")