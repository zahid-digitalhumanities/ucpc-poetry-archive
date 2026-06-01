from flask import Blueprint, render_template
from models.db import get_db

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    """Homepage with statistics"""
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

    # Get total readers (sum of views from texts table)
    cur.execute("SELECT COALESCE(SUM(views), 0) as total FROM texts")
    total_readers = cur.fetchone()
    readers_count = total_readers['total'] if total_readers else 0

    cur.close()
    conn.close()

    return render_template('index.html',
                         total_poets=poets_count,
                         total_ghazals=ghazals_count,
                         total_readers=readers_count)