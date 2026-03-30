from flask import Blueprint, send_file, abort
import os

# Models
from models.listen_model import generate_audio
from models.ghazal_model import get_ghazal_with_verses

listen_bp = Blueprint('listen', __name__)


@listen_bp.route("/listen/<int:text_id>")
def listen(text_id):
    print(f"🎧 Listen request for ID: {text_id}")

    try:
        ghazal, verses = get_ghazal_with_verses(text_id)

        if not ghazal:
            print("❌ Ghazal not found")
            abort(404)

        urdu_text = ghazal.get("text_urdu", "")
        english_text = ghazal.get("text_english", "")

        print("✅ Text fetched")

        filepath = generate_audio(text_id, urdu_text, english_text)

        if not filepath or not os.path.exists(filepath):
            print("❌ Audio generation failed")
            abort(500)

        print("✅ Audio ready:", filepath)

        return send_file(filepath, mimetype="audio/mpeg")

    except Exception as e:
        print("🔥 ERROR in listen route:", str(e))
        abort(500)