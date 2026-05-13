# models/ai_engine/poet_prediction_ai_v2.py
"""
UCPC Poet Attribution Engine - Fixed with HACK
Research-grade with explainability, honest confidence, and reproducibility logging
"""

import os
import sys
import pickle
import re
import json
import numpy as np
from typing import List, Dict, Any
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, BASE_DIR)

from models.base import get_db_connection
import models.vectorizers as vec
from modules.explainability import explain_prediction

# ========== RESEARCH LOGGING SETUP ==========
LOG_DIR = os.path.join(BASE_DIR, 'logs', 'research')
os.makedirs(LOG_DIR, exist_ok=True)

# Corpus and model versioning for reproducibility
CORPUS_VERSION = "1.2"      # Update when corpus changes
MODEL_VERSION = "v9"         # Update when model changes


def log_prediction(text: str, predictions: List[Dict], text_length: int, confidence: float = 0):
    """
    Log prediction for research reproducibility.
    Saves to logs/research/predictions_YYYYMMDD.jsonl
    """
    try:
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "text_length": text_length,
            "corpus_version": CORPUS_VERSION,
            "model_version": MODEL_VERSION,
            "confidence": confidence,
            "top_prediction": predictions[0] if predictions else None,
            "num_predictions": len(predictions),
            "prediction_summary": [
                {
                    "poet_name": p.get("poet_name"),
                    "confidence": p.get("confidence_percent")
                }
                for p in predictions[:3]
            ]
        }
        log_file = os.path.join(LOG_DIR, f"predictions_{datetime.now().strftime('%Y%m%d')}.jsonl")
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')
    except Exception as e:
        print(f"⚠️ Research logging error: {e}")


# ========== CRITICAL HACK: Make vectorizers available to pickle ==========
# This allows loading the existing v9 model without retraining
sys.modules['__main__'].HybridVectorizer = vec.HybridVectorizer
sys.modules['__main__'].AdvancedTextVectorizer = vec.AdvancedTextVectorizer
# =========================================================================


def load_model():
    """Load trained model from models/ml/ directory"""
    model_path = os.path.join(BASE_DIR, 'models', 'ml', 'poet_classifier_v9.pkl')
    
    # Also try v8 if v9 fails
    if not os.path.exists(model_path):
        model_path = os.path.join(BASE_DIR, 'models', 'ml', 'poet_classifier_v8.pkl')
    
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"No model found in {BASE_DIR}/models/ml/")
    
    with open(model_path, 'rb') as f:
        model = pickle.load(f)
    
    print(f"✅ Loaded: {os.path.basename(model_path)}")
    print(f"   Accuracy: {model.get('accuracy', 0):.2%}")
    return model


def normalize_urdu(text: str) -> str:
    if not text:
        return ""
    text = text.strip()
    replacements = {'ي': 'ی', 'ك': 'ک', 'ة': 'ہ', 'أ': 'ا', 'إ': 'ا', 'آ': 'ا'}
    for old, new in replacements.items():
        text = text.replace(old, new)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def split_into_ashaar(text: str) -> List[str]:
    lines = [l.strip() for l in text.split('\n') if l.strip()]
    ashaar = []
    for i in range(0, len(lines) - 1, 2):
        sher = f"{lines[i]}\n{lines[i+1]}".strip()
        if len(sher) > 20:
            ashaar.append(sher)
    return ashaar if ashaar else [text]


def get_poet_name(poet_id: int) -> str:
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT name FROM poets WHERE id = %s", (poet_id,))
        row = cur.fetchone()
        cur.close()
        conn.close()
        if row:
            if hasattr(row, 'keys'):
                return row['name']
            else:
                return row[0]
        return f"Poet_{poet_id}"
    except Exception as e:
        print(f"⚠️ Could not get poet name: {e}")
        return f"Poet_{poet_id}"


def predict_poet_from_text(text: str, top_n: int = 5) -> List[Dict[str, Any]]:
    """
    Predict poet from Urdu ghazal text.
    Returns predictions with confidence scores, explainability, and logs for research.
    """
    try:
        text_length = len(text.strip())
        
        # =====================================================
        # SHORT TEXT STRATEGY (Academic honesty)
        # =====================================================
        if not text or text_length < 100:
            result = [{
                "poet_name": "Insufficient Text",
                "poet_name_urdu": "",
                "confidence": 0,
                "confidence_percent": 0,
                "confidence_level": "uncertain",
                "match_type": "error",
                "method": "ml_ensemble",
                "evidence": [],
                "explanation": ["Provide at least 100 characters for reliable attribution"],
                "error": f"Text too short ({text_length} chars). Minimum 100 characters required."
            }]
            # Log even failed predictions for research
            log_prediction(text, result, text_length, 0)
            return result

        # Load model
        model_pkg = load_model()
        model = model_pkg['model']
        vectorizer = model_pkg['vectorizer']
        label_encoder = model_pkg['label_encoder']
        
        # Normalize and split
        text_norm = normalize_urdu(text)
        ashaar = split_into_ashaar(text_norm)
        
        # Aggregate predictions across shers
        aggregated_probs = None
        for sher in ashaar:
            X = vectorizer.transform([sher])
            probs = model.predict_proba(X)[0]
            if aggregated_probs is None:
                aggregated_probs = probs
            else:
                aggregated_probs += probs
        
        aggregated_probs = aggregated_probs / len(ashaar)
        top_indices = np.argsort(aggregated_probs)[::-1][:top_n]
        
        results = []
        top_confidence = 0.0
        
        for idx in top_indices:
            confidence = float(aggregated_probs[idx])
            poet_id = int(label_encoder.inverse_transform([idx])[0])
            poet_name = get_poet_name(poet_id)
            
            if confidence > top_confidence:
                top_confidence = confidence
            
            # =====================================================
            # HONEST CONFIDENCE CALIBRATION (Academic standard)
            # =====================================================
            if confidence >= 0.75:
                conf_level = "high"
            elif confidence >= 0.50:
                conf_level = "moderate"
            elif confidence >= 0.35:
                conf_level = "low"
            else:
                conf_level = "uncertain"
            
            # Keep original poet name - don't replace with "Uncertain Attribution"
            # Instead, add a confidence indicator in the name for very low confidence
            display_name = poet_name
            if confidence < 0.35:
                display_name = f"{poet_name} (Low Confidence)"
            
            confidence_percent = round(confidence * 100, 2)
            
            # =====================================================
            # EXPLAINABILITY LAYER (Research-grade)
            # =====================================================
            explanation = explain_prediction(poet_name)
            
            results.append({
                "poet_id": poet_id,
                "poet_name": display_name,  # Use display name with indicator if needed
                "poet_name_urdu": "",
                "confidence": confidence_percent,
                "confidence_percent": confidence_percent,
                "confidence_level": conf_level,
                "match_type": "stylometric_prediction",
                "method": "ml_ensemble",
                "evidence": [],
                "explanation": explanation
            })
        
        # =====================================================
        # RESEARCH LOGGING (Reproducibility)
        # =====================================================
        log_prediction(text, results, text_length, top_confidence)
        
        return results
    
    except Exception as e:
        print(f"❌ Prediction Error: {e}")
        import traceback
        traceback.print_exc()
        error_result = [{
            "poet_name": "Prediction Failed",
            "poet_name_urdu": "",
            "confidence": 0,
            "confidence_percent": 0,
            "confidence_level": "uncertain",
            "match_type": "error",
            "method": "ml_ensemble",
            "evidence": [],
            "explanation": [f"Prediction system error: {str(e)}"],
            "error": str(e)
        }]
        # Log error for research tracking
        log_prediction(text, error_result, len(text), 0)
        return error_result


def get_model_info() -> Dict:
    """Get information about the loaded model with versioning"""
    try:
        model_pkg = load_model()
        return {
            "loaded": True,
            "accuracy": model_pkg.get('accuracy', 'N/A'),
            "num_poets": model_pkg.get('num_poets', 'N/A'),
            "training_date": model_pkg.get('training_date', 'Unknown'),
            "version": model_pkg.get('version', 'v9'),
            "corpus_version": CORPUS_VERSION,
            "model_version": MODEL_VERSION,
            "research_logging_enabled": True,
            "log_directory": LOG_DIR
        }
    except Exception as e:
        return {"loaded": False, "error": str(e)}


# =========================================================
# TEST
# =========================================================
if __name__ == "__main__":
    test = "دل ہی تو ہے نہ سنگ و خشت، درد سے بھر نہ آئے کیوں"
    print("=" * 60)
    print("Testing Poet Prediction with Research Logging")
    print("=" * 60)
    results = predict_poet_from_text(test, top_n=3)
    for r in results:
        print(f"\n📝 {r['poet_name']}: {r['confidence_percent']}% ({r['confidence_level']})")
        if r.get('explanation'):
            print(f"   Evidence: {', '.join(r['explanation'][:3])}")
    
    # Show log location
    print(f"\n📊 Research logs saved to: {LOG_DIR}")