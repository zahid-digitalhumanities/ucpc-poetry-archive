# routes/main_routes.py
from flask import Blueprint, render_template
from models.stats_model import get_stats
from models.poets_model import get_all_poets
from models.ghazal_model import get_recent_ghazals
from models.base import get_db_connection
import os

main_bp = Blueprint('main', __name__)

def get_sample_couplet_for_poet(poet_id):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            SELECT v.misra1_urdu, v.misra2_urdu
            FROM verses v
            JOIN texts t ON v.text_id = t.id
            WHERE t.poet_id = %s AND t.form = 'ghazal'
            ORDER BY t.id, v.couplet_index
            LIMIT 1
        """, (poet_id,))
        row = cur.fetchone()
        if row and row.get('misra1_urdu'):
            return f"{row['misra1_urdu']}<br>{row['misra2_urdu']}"
    except Exception:
        # Silently ignore (poet has no ghazal/verse)
        pass
    finally:
        cur.close()
        conn.close()
    return "✨"

@main_bp.route('/')
def index():
    stats = get_stats()
    poets_data = get_all_poets()
    poets = []
    for p in poets_data:
        poets.append({
            'id': p['id'],
            'name': p['name'],
            'name_urdu': p.get('name_urdu', ''),
            'image_filename': None,
            'display_couplet': get_sample_couplet_for_poet(p['id']),
            'ghazal_count': p.get('ghazal_count', 0)   # 🔥 passes ghazal count to template
        })
    recent_ghazals = get_recent_ghazals(limit=10)
    return render_template('index.html', poets=poets, recent_ghazals=recent_ghazals, stats=stats)

# ================= NEW RESEARCH DASHBOARD ROUTE =================
@main_bp.route('/research')
def research_dashboard():
    """Render the AI research dashboard (ask_ucpc.html)."""
    return render_template('ask_ucpc.html')