from flask import Blueprint, render_template
from models.poets_model import fetch_all_poets
from models.stats_model import get_stats

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    stats = get_stats()
    poets = fetch_all_poets()
    return render_template('index.html', poets=poets, stats=stats)
