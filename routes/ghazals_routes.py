from flask import Blueprint, render_template, abort
from models.db import get_db

ghazals_bp = Blueprint('ghazals', __name__)


@ghazals_bp.route('/view/<int:text_id>')
def view_ghazal(text_id):
    """Display a single ghazal with all its verses"""
    conn = get_db()
    cur = conn.cursor()

    # Get ghazal info from texts table
    # Note: poet_name doesn't exist, so we join with poets table
    cur.execute("""
        SELECT 
            t.id,
            t.title_urdu,
            t.title_en,
            t.verse_count,
            t.first_line,
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

    # Get all verses for this ghazal from verses table
    # Note: Using couplet_index instead of verse_number
    cur.execute("""
        SELECT 
            id,
            text_id,
            couplet_index as verse_number,
            misra1_urdu,
            misra2_urdu,
            misra1_english,
            misra2_english,
            is_matla,
            is_maqta
        FROM verses
        WHERE text_id = %s
        ORDER BY couplet_index ASC
    """, (text_id,))
    
    verses = cur.fetchall()

    cur.close()
    conn.close()

    return render_template('view.html', ghazal=ghazal, verses=verses)
