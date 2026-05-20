from flask import Blueprint, render_template, abort
from models.db import get_db

poets_bp = Blueprint('poets', __name__)


@poets_bp.route('/')
def poets_list():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT p.id, p.name, p.name_urdu, COUNT(t.id) as ghazal_count
        FROM poets p
        LEFT JOIN texts t ON p.id = t.poet_id
        GROUP BY p.id, p.name, p.name_urdu
        ORDER BY p.name ASC
    """)
    poets = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('poets.html', poets=poets)


@poets_bp.route('/<int:poet_id>')
def poet_detail(poet_id):
    conn = get_db()
    cur = conn.cursor()

    # Get poet info
    cur.execute("""
        SELECT id, name, name_urdu, birth_year, death_year
        FROM poets WHERE id = %s
    """, (poet_id,))
    poet = cur.fetchone()

    if poet is None:
        cur.close()
        conn.close()
        abort(404)

    # Get ghazals with FIRST VERSE from verses table
    cur.execute("""
        SELECT 
            t.id,
            t.verse_count,
            COALESCE(t.first_line, '') as first_couplet,
            v.misra1_urdu,
            v.misra2_urdu
        FROM texts t
        LEFT JOIN verses v ON v.text_id = t.id AND v.couplet_index = 1
        WHERE t.poet_id = %s
        ORDER BY t.id DESC
    """, (poet_id,))
    
    texts = cur.fetchall()
    cur.close()
    conn.close()

    return render_template('poet_detail.html', 
                          poet=poet, 
                          texts=texts,
                          total=len(texts))