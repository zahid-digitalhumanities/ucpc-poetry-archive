from flask import Blueprint, send_file, abort
import os

from models.listen_model import generate_audio
from models.ghazal_model import get_ghazal_with_verses

# ✅ IMPORTANT: url_prefix use کرو
listen_bp = Blueprint('listen', __name__, url_prefix='/listen')


@listen_bp.route('/<int:text_id>')
def listen(text_id):
    print(f"🎧 Listen request: {text_id}")

    ghazal, verses = get_ghazal_with_verses(text_id)

    if not ghazal:
        print("❌ Ghazal not found")
        abort(404)

    urdu_text = ghazal.get("text_urdu", "")
    english_text = ghazal.get("text_english", "")

    filepath = generate_audio(text_id, urdu_text, english_text)

    if not filepath or not os.path.exists(filepath):
        print("❌ Audio failed")
        abort(500)

    print("✅ Audio ready")

    return send_file(filepath, mimetype="audio/mpeg")