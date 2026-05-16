from flask import Blueprint, render_template, request
from models.poets_model import fetch_all_poets
from models.stats_model import get_stats
from models.ghazals_model import get_recent_ghazals  # Add this import

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    stats = get_stats()
    poets = fetch_all_poets()
    recent_ghazals = get_recent_ghazals(limit=5)  # Fetch 5 recent ghazals
    return render_template('index.html', 
                         poets=poets, 
                         stats=stats, 
                         recent_ghazals=recent_ghazals,
                         request=request)
