from flask import Blueprint, render_template, abort, jsonify, redirect, url_for
from modules.poster.poster_service import PosterService

ghazals_bp = Blueprint('ghazals', __name__)


# =====================================================
# POSTER PAGE (using modular service)
# =====================================================

@ghazals_bp.route('/poster/<int:text_id>')
def poster_page(text_id):
    """Generate poster with up to 4 couplets using modular service"""
    data = PosterService.build_poster_data(text_id, couplet_limit=4)

    if data is None:
        abort(404)

    return render_template('poster.html',
                          ghazal=data['ghazal'],
                          poster_verses=data['poster_verses'])


# The rest of your routes (ghazal_page, view_redirect, etc.) remain UNCHANGED.
