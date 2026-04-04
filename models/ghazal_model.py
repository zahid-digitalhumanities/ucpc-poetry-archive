from flask import Blueprint, render_template, flash, redirect, url_for
from models.poets_model import fetch_poet_by_id, fetch_all_poets
from models.ghazal_model import fetch_texts_by_poet   # ✅ use existing function
from models.stats_model import get_stats

poets_bp = Blueprint('poets', __name__)

@poets_bp.route('/poets')
def poets_list():
    stats = get_stats()
    poets = fetch_all_poets()
    return render_template('poets.html', poets=poets, stats=stats)

@poets_bp.route('/poet/<int:poet_id>')
def poet_detail(poet_id):
    poet = fetch_poet_by_id(poet_id)
    if not poet:
        flash('Poet not found', 'error')
        return redirect(url_for('main.index'))
    texts = fetch_texts_by_poet(poet_id)   # ✅ returns list of texts for this poet
    return render_template('poet_detail.html', poet=poet, texts=texts)
