from flask import Blueprint, render_template
from models.ghazal_model import get_ghazal, get_verses

ghazal_bp = Blueprint('ghazal', __name__)

@ghazal_bp.route('/view/<int:id>')
def view_ghazal(id):
    ghazal = get_ghazal(id)
    verses = get_verses(id)

    return render_template('view.html', ghazal=ghazal, verses=verses)