from flask import Blueprint, render_template, abort
from models.poets_model import fetch_poet_by_id, fetch_all_poets
from models.ghazals_model import fetch_texts_by_poet
from models.stats_model import get_stats

poets_bp = Blueprint('poets', __name__)

@poets_bp.route('/poets')
def poets_list():
    stats = get_stats()
    poets = fetch_all_poets()
    return render_template('poets.html', poets=poets, stats=stats)

@poets_bp.route('/poet/<int:poet_id>')
def poet_detail(poet_id):
    stats = get_stats()
    poet = fetch_poet_by_id(poet_id)
    if not poet:
        abort(404)
    texts = fetch_texts_by_poet(poet_id)
    radif_summary = []
    qaafiya_summary = []
    return render_template('poet_detail.html',
                           poet=poet,
                           texts=texts,
                           stats=stats,
                           radif_summary=radif_summary,
                           qaafiya_summary=qaafiya_summary)