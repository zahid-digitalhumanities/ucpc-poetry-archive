# routes/main_routes.py
from flask import Blueprint, render_template
from models.stats_model import get_stats
from models.poets_model import fetch_poets_with_sample
from models.ghazal_model import get_db
import os

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    stats = get_stats()
    
    # 1. Fetch all poets with a sample text for the home page grid
    poets_data = fetch_poets_with_sample()
    poets = []
    for p in poets_data:
        img_filename = None
        id_path = f"images/poets/{p['id']}.jpg"
        name_path = f"images/poets/{p['name'].replace(' ', '_')}.jpg"
        if os.path.exists(os.path.join('static', id_path)):
            img_filename = f"{p['id']}.jpg"
        elif os.path.exists(os.path.join('static', name_path)):
            img_filename = f"{p['name'].replace(' ', '_')}.jpg"
        poets.append({
            'id': p['id'],
            'name': p['name'],
            'name_urdu': p['name_urdu'],
            'image_filename': img_filename,
            'text_urdu': p['text_urdu']
        })
    
    # 2. Fetch recent ghazals from the `texts` table (not `ghazals`)
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT t.id, t.title_english, t.title_urdu, p.name as poet_name
        FROM texts t
        JOIN poets p ON t.poet_id = p.id
        WHERE t.text_urdu IS NOT NULL
        ORDER BY t.created_at DESC
        LIMIT 10
    """)
    recent_ghazals = cur.fetchall()
    cur.close()
    conn.close()
    
    return render_template('index.html', poets=poets, recent_ghazals=recent_ghazals, stats=stats)