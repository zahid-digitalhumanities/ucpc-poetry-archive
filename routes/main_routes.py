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

    # Get recent ghazals (last 6)
    cur.execute("""
        SELECT t.id, t.first_couplet, t.poet_id,
               p.name as poet_name
        FROM texts t
        LEFT JOIN poets p ON t.poet_id = p.id
        WHERE t.first_couplet IS NOT NULL
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