from flask import Blueprint, render_template, abort
from models.ghazal_model import get_ghazal_with_verses, get_navigation

ghazals_bp = Blueprint('ghazals', __name__, url_prefix='/ghazals')

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
    prev_id, next_id, total = get_navigation(text_id, ghazal['poet_id'])
    return render_template('view.html', ghazal=ghazal, verses=verses, prev_id=prev_id, next_id=next_id, total=total)

# Add other routes (add_ghazal, etc.) as needed
