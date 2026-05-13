# routes/research_dashboard.py

from flask import Blueprint, render_template, request, jsonify
import traceback
import time
import re

from models.ai_engine.poet_prediction_ai_v2 import predict_poet_from_text

# =========================================================
# OPTIONAL MODULE IMPORTS
# =========================================================

# Semantic similarity
try:
    from models.ai_engine.similarity_model import find_similar_by_text
except Exception:
    find_similar_by_text = None

# Theme analysis
try:
    from modules.theme import analyze_theme
except Exception:
    analyze_theme = None

# Radif / Qaafiya
try:
    from modules.radif_qaafiya import extract_radif_qaafiya
except Exception:
    extract_radif_qaafiya = None

# Stylometry
try:
    from modules.stylometry import generate_stylometric_features
except Exception:
    generate_stylometric_features = None

# Preprocessing metrics
try:
    from modules.preprocessing_analysis import corpus_metrics
except Exception:
    corpus_metrics = None


# =========================================================
# BLUEPRINT
# =========================================================

research_dashboard_bp = Blueprint(
    'research_dashboard',
    __name__,
    url_prefix='/research'
)


# =========================================================
# HELPERS
# =========================================================

def safe_text(text):
    if not text:
        return ""

    text = str(text)

    # normalize whitespace
    text = re.sub(r'\s+', ' ', text)

    return text.strip()


def confidence_label(score):
    """
    Research-grade interpretation labels
    """

    try:
        score = float(score)
    except:
        return "Unknown"

    if score >= 0.85:
        return "Strong Attribution"

    if score >= 0.65:
        return "Moderate Attribution"

    if score >= 0.45:
        return "Weak Attribution"

    return "Uncertain Prediction"


# =========================================================
# DASHBOARD PAGE
# =========================================================

@research_dashboard_bp.route('/')
def dashboard():
    """
    Main research dashboard page
    """
    return render_template('research_dashboard.html')


# =========================================================
# MAIN RESEARCH ANALYSIS API
# =========================================================

@research_dashboard_bp.route('/api/analyze', methods=['POST'])
def analyze_text():

    started = time.time()

    try:

        payload = request.get_json() or {}

        text = safe_text(payload.get('text'))

        if not text:
            return jsonify({
                "success": False,
                "error": "No text provided"
            }), 400

        # =====================================================
        # BASIC CORPUS METADATA
        # =====================================================

        char_count = len(text)

        token_count = len(text.split())

        verse_count = len([
            x for x in text.split('\n')
            if x.strip()
        ])

        # =====================================================
        # AUTHORSHIP ATTRIBUTION
        # =====================================================

        poet_predictions = []

        try:

            poet_predictions = predict_poet_from_text(
                text=text,
                top_n=5
            )

            # add interpretation labels
            for p in poet_predictions:

                confidence = p.get("confidence", 0)

                p["interpretation"] = confidence_label(
                    confidence
                )

                # research disclaimer
                p["scholarly_note"] = (
                    "Computational authorship attribution "
                    "is probabilistic and corpus-based."
                )

        except Exception as e:
            print("❌ Poet prediction error:", e)

        # =====================================================
        # THEMATIC ANALYSIS
        # =====================================================

        theme_result = {}

        try:

            if analyze_theme:

                theme_result = analyze_theme(text)

        except Exception as e:
            print("❌ Theme analysis error:", e)

        # =====================================================
        # RADIF / QAAFIYA
        # =====================================================

        prosody_result = {}

        try:

            if extract_radif_qaafiya:

                prosody_result = extract_radif_qaafiya(text)

        except Exception as e:
            print("❌ Prosody extraction error:", e)

        # =====================================================
        # SEMANTIC RETRIEVAL
        # =====================================================

        semantic_results = []

        try:

            if find_similar_by_text:

                semantic_results = find_similar_by_text(
                    text=text,
                    top_n=10
                )

        except Exception as e:
            print("❌ Semantic retrieval error:", e)

        # =====================================================
        # STYLOMETRIC ANALYSIS
        # =====================================================

        stylometry = {}

        try:

            if generate_stylometric_features:

                stylometry = generate_stylometric_features(
                    text
                )

        except Exception as e:
            print("❌ Stylometry error:", e)

        # =====================================================
        # PREPROCESSING METRICS
        # =====================================================

        preprocessing = {}

        try:

            if corpus_metrics:

                preprocessing = corpus_metrics(text)

        except Exception as e:
            print("❌ Preprocessing metrics error:", e)

        # =====================================================
        # RESEARCH METADATA
        # =====================================================

        runtime = round(
            time.time() - started,
            2
        )

        metadata = {
            "framework":
                "UCPC Digital Humanities Infrastructure",

            "methods": [
                "Character N-Gram Stylometry",
                "TF-IDF Lexical Attribution",
                "Semantic Embedding Retrieval",
                "Rule-Based Urdu Prosody",
                "Corpus-Based Literary Analysis"
            ],

            "runtime_seconds": runtime,

            "corpus_statistics": {
                "canonical_ghazals": 5194,
                "annotated_shers": 28372,
                "retrieval_mode": "Urdu + Roman Urdu",
                "search_capabilities": [
                    "Matla Search",
                    "Sher Search",
                    "Semantic Search",
                    "Stylometric Attribution"
                ]
            }
        }

        # =====================================================
        # FINAL RESPONSE
        # =====================================================

        return jsonify({

            "success": True,

            # =================================================
            # INPUT METADATA
            # =================================================

            "input_analysis": {
                "character_count": char_count,
                "token_count": token_count,
                "verse_count": verse_count,
                "language": "Urdu",
                "normalized": True
            },

            # =================================================
            # AUTHORSHIP
            # =================================================

            "poet_prediction": {
                "method":
                    "Explainable Ensemble Stylometric Attribution",

                "results": poet_predictions
            },

            # =================================================
            # THEMES
            # =================================================

            "themes": {
                "method":
                    "Computational Thematic Modeling",

                "data": theme_result
            },

            # =================================================
            # SEMANTIC RETRIEVAL
            # =================================================

            "semantic_matches": {
                "method":
                    "Transformer Semantic Retrieval",

                "results": semantic_results
            },

            # =================================================
            # PROSODY
            # =================================================

            "prosody": {
                "method":
                    "Rule-Based Urdu Prosodic Analysis",

                "data": prosody_result
            },

            # =================================================
            # STYLOMETRY
            # =================================================

            "stylometry": stylometry,

            # =================================================
            # PREPROCESSING
            # =================================================

            "preprocessing": preprocessing,

            # =================================================
            # RESEARCH METADATA
            # =================================================

            "research_metadata": metadata
        })

    except Exception as e:

        traceback.print_exc()

        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# =========================================================
# HEALTH CHECK
# =========================================================

@research_dashboard_bp.route('/api/health')
def health_check():

    return jsonify({
        "status": "ok",
        "module": "UCPC Research Dashboard",
        "framework": "Digital Humanities Infrastructure"
    })