from flask import Blueprint, render_template, request
from models.poets_model import fetch_all_poets
from models.stats_model import get_stats
from models.ghazal_model import get_recent_ghazals  # ✅ Fixed: ghazal_model (not ghazals_model)

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    stats = get_stats()
    poets = fetch_all_poets()
    recent_ghazals = get_recent_ghazals(limit=5)
    return render_template('index.html', 
                         poets=poets, 
                         stats=stats, 
                         recent_ghazals=recent_ghazals,
                         request=request)
