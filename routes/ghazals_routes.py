# routes/ghazals_routes.py
from flask import Blueprint, render_template, abort, jsonify
from models.ghazal_model import (
    get_ghazal_with_verses, get_navigation, get_books_by_poet
)

ghazals_bp = Blueprint('ghazals', __name__, url_prefix='/ghazals')

# ================= VIEW GHAZAL =================
@ghazals_bp.route('/view/<int:text_id>')
def view_ghazal(text_id):
    result = get_ghazal_with_verses(text_id)
    if not result:
        abort(404)
    if isinstance(result, tuple):
        ghazal, verses = result
    else:
        ghazal = result.get('ghazal')
        verses = result.get('verses')
    if not ghazal:
        abort(404)
    prev_id, next_id, total = get_navigation(text_id, ghazal['poet_id'])
    return render_template(
        'view.html',
        ghazal=ghazal,
        verses=verses,
        prev_id=prev_id,
        next_id=next_id,
        total=total
    )

# ================= BOOKS (AJAX) =================
@ghazals_bp.route('/books/<int:poet_id>')
def get_books(poet_id):
    books = get_books_by_poet(poet_id)
    return jsonify({'books': books})