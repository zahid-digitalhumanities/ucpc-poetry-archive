# routes/ask_ucpc_index.py
"""
UCPC Research API
-----------------

Research-grade Digital Humanities analysis endpoint.
"""

from flask import Blueprint, request, jsonify
import os
import sys
import traceback
import re

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

# =========================================================
# IMPORTS
# =========================================================

from models.ai_engine.poet_prediction_ai_v2 import (
    predict_poet_from_text,
    get_model_info
)

# Optional imports with fallbacks
try:
    from modules.theme import detect_theme, detect_multiple_themes, extract_theme_keywords
except ImportError:
    detect_theme = lambda x: "unknown"
    detect_multiple_themes = lambda x: []
    extract_theme_keywords = lambda x: []

try:
    from modules.radif_qaafiya import extract_radif_qaafiya, process_ghazal
except ImportError:
    extract_radif_qaafiya = lambda x: {"radif": None, "qaafiya": [], "confidence": 0.0}
    process_ghazal = lambda x, y: {}

try:
    from modules.stylometry import extract_stylometric_signature, quick_stylometric_profile
except ImportError:
    extract_stylometric_signature = lambda x: {}
    quick_stylometric_profile = lambda x: {}

try:
    from modules.preprocessing_analysis import preprocess_urdu_text, corpus_metrics
except ImportError:
    def preprocess_urdu_text(text):
        return {"normalized_text": text, "token_count": len(text.split())}
    corpus_metrics = lambda x: {}

try:
    from modules.semantic_intertextual import semantic_search, detect_intertextual_links
except ImportError:
    semantic_search = lambda x, y: []
    detect_intertextual_links = lambda x, y: []

ask_ucpc_bp = Blueprint("ask_ucpc", __name__, url_prefix="/ask-index")


# =========================================================
# HELPER FUNCTIONS
# =========================================================

def normalize_question(question: str) -> str:
    if not question:
        return ""
    q = question.lower().strip()
    q = re.sub(r'[؟؟!?,.;:]', '', q)
    return q


def get_analysis_type(question: str) -> str:
    q = normalize_question(question)
    if any(word in q for word in ['poet', 'author', 'shayar', 'شاعر', 'writer', 'whose', 'kis', 'likhi']):
        return "poet"
    if any(word in q for word in ['theme', 'موضوع', 'thematic', 'topic', 'mood', 'emotion']):
        return "theme"
    if any(word in q for word in ['radif', 'qaafiya', 'prosody', 'meter', 'rhyme', 'refrain', 'قافیہ', 'ردیف']):
        return "prosody"
    if any(word in q for word in ['similar', 'semantic', 'like this', 'find similar', 'مشابہ']):
        return "semantic"
    if any(word in q for word in ['intertextual', 'influence', 'link', 'connection', 'اثر']):
        return "intertextual"
    if any(word in q for word in ['stylometry', 'style', 'writing style', 'اسلوب']):
        return "stylometry"
    if any(word in q for word in ['full', 'complete', 'all', 'comprehensive', 'مکمل']):
        return "full"
    return "poet"


# =========================================================
# HEALTH & INFO
# =========================================================

@ask_ucpc_bp.route("/health", methods=["GET"])
def health():
    try:
        info = get_model_info()
        return jsonify({
            "status": "ok",
            "module": "UCPC Research API",
            "model_loaded": info.get("loaded", False),
            "model_accuracy": info.get("accuracy", "N/A"),
            "num_poets": info.get("num_poets", "N/A")
        })
    except Exception as e:
        return jsonify({"status": "degraded", "error": str(e)}), 500


@ask_ucpc_bp.route("/")
def index():
    return jsonify({
        "status": "ok",
        "module": "UCPC Research API",
        "endpoints": {
            "POST /": "Main analysis endpoint",
            "GET /health": "Health check",
            "GET /model-info": "Model information"
        }
    })


@ask_ucpc_bp.route("/model-info", methods=["GET"])
def model_info_endpoint():
    try:
        info = get_model_info()
        return jsonify(info)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# =========================================================
# MAIN ANALYSIS ROUTE
# =========================================================

@ask_ucpc_bp.route("/", methods=["POST"])
def ask_index():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "No JSON data provided"}), 400

        text = data.get("text", "").strip()
        question = data.get("question", "").strip()

        if not question:
            analysis_type = "full" if len(text) > 100 else "poet"
        else:
            analysis_type = get_analysis_type(question)

        if not text:
            return jsonify({"success": False, "error": "No text provided"}), 400

        # Preprocess
        try:
            processed = preprocess_urdu_text(text)
            normalized_text = processed.get("normalized_text", text)
        except Exception:
            normalized_text = text

        # =================================================
        # POET ATTRIBUTION
        # =================================================
        if analysis_type == "poet":
            predictions = predict_poet_from_text(normalized_text, top_n=5)

            if not predictions:
                return jsonify({"success": False, "error": "Prediction failed"}), 500

            enriched = []
            for p in predictions:
                enriched.append({
                    "poet_id": p.get("poet_id"),
                    "poet_name": p.get("poet_name"),
                    "poet_name_urdu": p.get("poet_name_urdu", ""),
                    "confidence": p.get("confidence", 0),
                    "confidence_percent": p.get("confidence", 0) * 100 if isinstance(p.get("confidence"), (int, float)) else 0,
                    "method": "Stylometric + TF-IDF"
                })

            return jsonify({
                "success": True,
                "analysis_type": "authorship_attribution",
                "method": "Research-grade stylometric attribution",
                "data": enriched,
                "metadata": {"input_length": len(normalized_text)}
            })

        # =================================================
        # FULL ANALYSIS
        # =================================================
        else:
            predictions = predict_poet_from_text(normalized_text, top_n=3)
            enriched_predictions = []
            for p in predictions[:3]:
                enriched_predictions.append({
                    "poet_name": p.get("poet_name"),
                    "confidence_percent": p.get("confidence", 0) * 100,
                    "confidence_level": "moderate"
                })

            return jsonify({
                "success": True,
                "analysis_type": "full_dh_pipeline",
                "method": "UCPC Research Stack v2",
                "data": {
                    "authorship": enriched_predictions,
                    "themes": {"primary": detect_theme(normalized_text), "additional": []},
                    "prosody": extract_radif_qaafiya(normalized_text),
                    "stylometry": quick_stylometric_profile(normalized_text) if quick_stylometric_profile else {}
                }
            })

    except Exception as e:
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500
