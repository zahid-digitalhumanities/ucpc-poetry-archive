from flask import Blueprint, render_template, abort
from models.db import get_db

ghazals_bp = Blueprint('ghazals', __name__)

@ghazals_bp.route('/view/<int:text_id>')
def view_ghazal(text_id):
    conn = get_db()
    cur = conn.cursor()

    # Get ghazal info
    cur.execute("""
        SELECT 
            t.id,
            t.verse_count,
            t.poet_id,
            p.name as poet_name,
            p.name_urdu as poet_name_urdu
        FROM texts t
        LEFT JOIN poets p ON t.poet_id = p.id
        WHERE t.id = %s
    """, (text_id,))
    
    ghazal = cur.fetchone()

    if ghazal is None:
        cur.close()
        conn.close()
        abort(404)

    # Get verses
    cur.execute("""
        SELECT misra1_urdu, misra2_urdu, couplet_index
        FROM verses
        WHERE text_id = %s
        ORDER BY couplet_index ASC
    """, (text_id,))
    
    all_verses = cur.fetchall()
    cur.close()
    conn.close()

    # For poster: ONLY FIRST 3 COUPLETS (fits 1080x1920 beautifully)
    poster_verses = all_verses[:3]

    return render_template('view.html', 
                          ghazal=ghazal, 
                          poster_verses=poster_verses)