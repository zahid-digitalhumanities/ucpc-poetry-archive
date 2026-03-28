from flask import Blueprint, send_file, abort
from models.listen_model import generate_audio
from models.ghazal_model import get_ghazal_by_id   # <-- adjust if needed

listen_bp = Blueprint('listen', __name__)

@listen_bp.route("/listen/<int:text_id>")
def listen(text_id):
    ghazal = get_ghazal_by_id(text_id)   # <-- adjust function name if needed
    if not ghazal:
        abort(404)
    urdu_text = ghazal.get("content_ur", "")      # <-- adjust keys if needed
    english_text = ghazal.get("translation_en", "") # <-- adjust keys if needed
    filepath = generate_audio(text_id, urdu_text, english_text)
    return send_file(filepath, mimetype="audio/mpeg")