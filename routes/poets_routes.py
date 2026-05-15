from flask import Blueprint, render_template, request, redirect, url_for
from models.base import get_db_connection

poets_bp = Blueprint('poets', __name__, url_prefix='/poets')

@poets_bp.route('/')
def poets_list():
    page = request.args.get('page', 1, type=int)
    per_page = 30
    offset = (page - 1) * per_page
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute("SELECT COUNT(*) as total FROM poets")
    total_row = cur.fetchone()
    total = total_row['total'] if total_row else 0
    
    cur.execute("""
        SELECT id, name, name_urdu, birth_year, death_year,
               (SELECT COUNT(*) FROM texts WHERE poet_id = poets.id AND form = 'ghazal' AND (is_deleted = FALSE OR is_deleted IS NULL)) as ghazal_count
        FROM poets 
        ORDER BY name
        LIMIT %s OFFSET %s
    """, (per_page, offset))
    
    poets = cur.fetchall()
    cur.close()
    conn.close()
    
    total_pages = (total + per_page - 1) // per_page if total > 0 else 1
    
    return render_template('poets.html', poets=poets, page=page, total_pages=total_pages, total=total)

@poets_bp.route('/<int:poet_id>')
def poet_detail(poet_id):
    page = request.args.get('page', 1, type=int)
    per_page = 20
    offset = (page - 1) * per_page
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute("""
        SELECT id, name, name_urdu, bio, birth_year, death_year
        FROM poets WHERE id = %s
    """, (poet_id,))
    poet = cur.fetchone()
    
    if not poet:
        cur.close()
        conn.close()
        return "Poet not found", 404
    
    cur.execute("""
        SELECT t.id, t.title_urdu, t.verse_count,
               (SELECT misra1_urdu FROM verses WHERE text_id = t.id AND couplet_index = 1 LIMIT 1) as misra1,
               (SELECT misra2_urdu FROM verses WHERE text_id = t.id AND couplet_index = 1 LIMIT 1) as misra2
        FROM texts t
        WHERE t.poet_id = %s AND t.form = 'ghazal' AND (t.is_deleted = FALSE OR t.is_deleted IS NULL)
        ORDER BY t.id DESC
        LIMIT %s OFFSET %s
    """, (poet_id, per_page, offset))
    texts = cur.fetchall()
    
    cur.execute("""
        SELECT COUNT(*) as total FROM texts 
        WHERE poet_id = %s AND form = 'ghazal' AND (t.is_deleted = FALSE OR t.is_deleted IS NULL)
    """, (poet_id,))
    total_row = cur.fetchone()
    total = total_row['total'] if total_row else 0
    
    cur.close()
    conn.close()
    
    for text in texts:
        if text['misra1']:
            text['first_verse'] = {
                'misra1_urdu': text['misra1'],
                'misra2_urdu': text['misra2'] or ''
            }
    
    total_pages = (total + per_page - 1) // per_page if total > 0 else 1
    
    return render_template('poet_detail.html', poet=poet, texts=texts, page=page, total_pages=total_pages, total=total)

@poets_bp.route('/poet/<int:poet_id>')
def poet_detail_alt(poet_id):
    return redirect(url_for('poets.poet_detail', poet_id=poet_id), 301)

@poets_bp.route('/poet/')
def poets_list_alt():
    return redirect(url_for('poets.poets_list'), 301)
