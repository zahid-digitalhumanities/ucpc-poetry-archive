from flask import Blueprint, send_file, abort
from models.listen_model import generate_audio
from models.ghazal_model import get_ghazal_with_verses

listen_bp = Blueprint('listen', __name__)

@listen_bp.route("/listen/<int:text_id>")
def listen(text_id):
    """
    Generate and stream ghazal audio
    """

    ghazal, verses = get_ghazal_with_verses(text_id)

    if not ghazal:
        abort(404)

    # ✅ correct fields
    urdu_text = ghazal.get("text_urdu", "")
    english_text = ghazal.get("text_english", "")

    filepath = generate_audio(text_id, urdu_text, english_text)

    if not filepath:
        abort(500)

    return send_file(filepath, mimetype="audio/mpeg")