from flask import Blueprint, render_template, request, abort
from models.base import get_db_connection

ghazals_bp = Blueprint('ghazals', __name__, url_prefix='/ghazals')

@ghazals_bp.route('/view/<int:text_id>')
def view_ghazal(text_id):
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Get ghazal details
    cur.execute("""
        SELECT t.id, t.title_urdu, t.verse_count, t.radif, t.qaafiya, t.theme,
               p.name as poet_name, p.name_urdu as poet_name_urdu, p.id as poet_id
        FROM texts t
        JOIN poets p ON t.poet_id = p.id
        WHERE t.id = %s AND t.form = 'ghazal' AND (t.is_deleted = FALSE OR t.is_deleted IS NULL)
    """, (text_id,))
    ghazal = cur.fetchone()
    
    if not ghazal:
        cur.close()
        conn.close()
        abort(404)
    
    # Get verses
    cur.execute("""
        SELECT misra1_urdu, misra2_urdu, couplet_index
        FROM verses
        WHERE text_id = %s
        ORDER BY couplet_index
    """, (text_id,))
    verses = cur.fetchall()
    
    # Get previous and next ghazal IDs for navigation
    cur.execute("""
        SELECT id FROM texts 
        WHERE poet_id = %s AND form = 'ghazal' AND (is_deleted = FALSE OR is_deleted IS NULL)
        ORDER BY id
    """, (ghazal['poet_id'],))
    all_ids = [row['id'] for row in cur.fetchall()]
    
    prev_id = None
    next_id = None
    for i, pid in enumerate(all_ids):
        if pid == text_id:
            if i > 0:
                prev_id = all_ids[i-1]
            if i < len(all_ids) - 1:
                next_id = all_ids[i+1]
            break
    
    cur.close()
    conn.close()
    
    return render_template('ghazal_view.html', 
                         ghazal=ghazal, 
                         verses=verses,
                         prev_id=prev_id,
                         next_id=next_id)
