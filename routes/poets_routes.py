from flask import Blueprint, render_template, request
from models.base import get_db_connection

poets_bp = Blueprint('poets', __name__, url_prefix='/poets')

@poets_bp.route('/')
def poets_list():
    page = request.args.get('page', 1, type=int)
    per_page = 30
    offset = (page - 1) * per_page
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Get total count
    cur.execute("SELECT COUNT(*) FROM poets ORDER BY name")
    total = cur.fetchone()['count']
    
    # Get poets with pagination
    cur.execute("""
        SELECT id, name, name_urdu, 
               birth_year, death_year,
               (SELECT COUNT(*) FROM texts WHERE poet_id = poets.id AND form = 'ghazal') as ghazal_count
        FROM poets 
        ORDER BY name
        LIMIT %s OFFSET %s
    """, (per_page, offset))
    
    poets = cur.fetchall()
    cur.close()
    conn.close()
    
    total_pages = (total + per_page - 1) // per_page
    
    return render_template('poets.html', 
                         poets=poets, 
                         page=page, 
                         total_pages=total_pages,
                         total=total)

@poets_bp.route('/<int:poet_id>')
def poet_detail(poet_id):
    page = request.args.get('page', 1, type=int)
    per_page = 20
    offset = (page - 1) * per_page
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Get poet info
    cur.execute("""
        SELECT id, name, name_urdu, bio, birth_year, death_year
        FROM poets WHERE id = %s
    """, (poet_id,))
    poet = cur.fetchone()
    
    if not poet:
        cur.close()
        conn.close()
        return "Poet not found", 404
    
    # Get poet's ghazals
    cur.execute("""
        SELECT id, title_urdu, verse_count
        FROM texts 
        WHERE poet_id = %s AND form = 'ghazal' AND (is_deleted = FALSE OR is_deleted IS NULL)
        ORDER BY id DESC
        LIMIT %s OFFSET %s
    """, (poet_id, per_page, offset))
    texts = cur.fetchall()
    
    # Get total count for pagination
    cur.execute("""
        SELECT COUNT(*) FROM texts 
        WHERE poet_id = %s AND form = 'ghazal' AND (is_deleted = FALSE OR is_deleted IS NULL)
    """, (poet_id,))
    total = cur.fetchone()['count']
    
    cur.close()
    conn.close()
    
    total_pages = (total + per_page - 1) // per_page
    
    return render_template('poet_detail.html',
                         poet=poet,
                         texts=texts,
                         page=page,
                         total_pages=total_pages,
                         total=total)
