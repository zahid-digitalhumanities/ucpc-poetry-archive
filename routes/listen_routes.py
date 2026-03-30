from flask import Blueprint, send_file, abort
import os

listen_bp = Blueprint('listen', __name__, url_prefix='/listen')

# 🧪 Test root
@listen_bp.route('/')
def listen_home():
    return "LISTEN ROOT OK"

# 🎧 Main route
@listen_bp.route('/<int:text_id>')
def listen(text_id):
    try:
        from models.listen_model import generate_audio
        from models.ghazal_model import get_ghazal_with_verses
    except Exception as e:
        return f"IMPORT ERROR: {str(e)}"

    ghazal, verses = get_ghazal_with_verses(text_id)

    if not ghazal:
        abort(404)

    urdu_text = ghazal.get("text_urdu", "")
    english_text = ghazal.get("text_english", "")

    filepath = generate_audio(text_id, urdu_text, english_text)

    if not filepath or not os.path.exists(filepath):
        return "AUDIO GENERATION FAILED"

    return send_file(filepath, mimetype="audio/mpeg")