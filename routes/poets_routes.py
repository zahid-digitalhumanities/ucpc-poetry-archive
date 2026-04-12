from flask import Blueprint, render_template, flash, redirect, url_for
from models.poets_model import fetch_poet_by_id, get_texts_with_first_verses
from models.ghazal_model import get_stats

poets_bp = Blueprint('poets', __name__)

@poets_bp.route('/poets')
def poets_list():
    from models.poets_model import fetch_all_poets
    poets = fetch_all_poets()
    stats = get_stats()
    return render_template('poets.html', poets=poets, stats=stats)

@poets_bp.route('/poet/<int:poet_id>')
def poet_detail(poet_id):
    poet = fetch_poet_by_id(poet_id)
    if not poet:
        flash('Poet not found', 'error')
        return redirect(url_for('main.index'))
    texts = get_texts_with_first_verses(poet_id)
    return render_template('poet_detail.html', poet=poet, texts=texts)
