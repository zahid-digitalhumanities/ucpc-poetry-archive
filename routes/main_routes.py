from flask import Blueprint, render_template
from models.stats_model import get_stats

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    stats = get_stats()
    return render_template('index.html', stats=stats)

@main_bp.route('/about')
def about():
    return render_template('about.html')
