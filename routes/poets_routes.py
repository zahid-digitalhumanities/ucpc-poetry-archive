from flask import Blueprint, render_template, flash, redirect, url_for

# ✅ Saare functions ek hi model se le rahe hain (no confusion)
from models.ghazal_model import (
    get_poet_by_id,
    get_all_poets,
    fetch_texts_by_poet,
    get_stats
)

poets_bp = Blueprint('poets', __name__)

# 📌 All poets list
@poets_bp.route('/poets')
def poets_list():
    stats = get_stats()
    poets = get_all_poets()
    return render_template('poets.html', poets=poets, stats=stats)

# 📌 Single poet detail
@poets_bp.route('/poet/<int:poet_id>')
def poet_detail(poet_id):
    poet = get_poet_by_id(poet_id)

    if not poet:
        flash('Poet not found', 'error')
        return redirect(url_for('main.index'))

    texts = fetch_texts_by_poet(poet_id)

    return render_template('poet_detail.html', poet=poet, texts=texts)