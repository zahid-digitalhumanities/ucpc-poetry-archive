from flask import Blueprint, render_template
from models.db import get_db

# Create the blueprint
main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    """Homepage with statistics and recent ghazals"""
    conn = get_db()
    cur = conn.cursor()

    # Get total poets count
    cur.execute("SELECT COUNT(*) as count FROM poets")
    total_poets = cur.fetchone()
    poets_count = total_poets['count'] if total_poets else 0

    # Get total ghazals count
    cur.execute("SELECT COUNT(*) as count FROM texts")
    total_ghazals = cur.fetchone()
    ghazals_count = total_ghazals['count'] if total_ghazals else 0

    # Get total readers
    cur.execute("SELECT COALESCE(SUM(views), 0) as total FROM texts")
    total_readers = cur.fetchone()
    readers_count = total_readers['total'] if total_readers else 0

    # Get recent ghazals with first verse from verses table
    cur.execute("""
        SELECT 
            t.id, 
            t.poet_id,
            COALESCE(p.name, 'Unknown Poet') as poet_name,
            v.misra1_urdu,
            v.misra2_urdu
        FROM texts t
        LEFT JOIN poets p ON t.poet_id = p.id
        LEFT JOIN verses v ON v.text_id = t.id AND v.couplet_index = 1
        WHERE v.misra1_urdu IS NOT NULL
        ORDER BY t.id DESC
        LIMIT 6
    """)
    recent_ghazals = cur.fetchall()

    cur.close()
    conn.close()

    if recent_ghazals is None:
        recent_ghazals = []

    return render_template('index.html',
                         total_poets=poets_count,
                         total_ghazals=ghazals_count,
                         total_readers=readers_count,
                         recent_ghazals=recent_ghazals)
