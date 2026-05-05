from flask import Blueprint, send_file
import os

listen_bp = Blueprint('listen', __name__, url_prefix='/listen')


@listen_bp.route('/<int:text_id>')
def listen(text_id):
    from models.listen_model import generate_audio
    from models.ghazal_model import get_ghazal_with_verses

    ghazal, _ = get_ghazal_with_verses(text_id)

    if not ghazal:
        return "❌ Ghazal not found", 404

    filepath = generate_audio(
        text_id,
        ghazal.get("text_urdu", ""),
        ghazal.get("text_english", "")
    )

    if not filepath or not os.path.exists(filepath):
        return "❌ Audio failed", 500

    return send_file(filepath, mimetype="audio/mpeg")