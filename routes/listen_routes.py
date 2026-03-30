from flask import Blueprint, send_file, abort
import os

listen_bp = Blueprint('listen', __name__, url_prefix='/listen')


# 🧪 Test route
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
        return "❌ Ghazal not found", 404

    urdu_text = ghazal.get("text_urdu", "")
    english_text = ghazal.get("text_english", "")

    filepath = generate_audio(text_id, urdu_text, english_text)

    print("="*50)
    print(f"FINAL FILEPATH: {filepath}")

    if not filepath or not os.path.exists(filepath):
        print("❌ AUDIO GENERATION FAILED")
        return "❌ AUDIO GENERATION FAILED", 500

    size = os.path.getsize(filepath)
    print(f"📦 FINAL FILE SIZE: {size} bytes")
    print("="*50)

    return send_file(filepath, mimetype="audio/mpeg")