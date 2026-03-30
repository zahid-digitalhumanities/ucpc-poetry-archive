from flask import Blueprint

listen_bp = Blueprint('listen', __name__, url_prefix='/listen')

@listen_bp.route('/')
def listen_home():
    return "LISTEN ROOT WORKING"

@listen_bp.route('/<int:text_id>')
def listen(text_id):
    return f"LISTEN ID: {text_id}"