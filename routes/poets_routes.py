from flask import Blueprint, render_template, abort
from models.db import get_db

poets_bp = Blueprint('poets', __name__)


@poets_bp.route('/')
def poets_list():
    """Display all poets with ghazal count"""
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT 
            p.id, 
            p.name, 
            p.name_urdu,
            COUNT(t.id) as ghazal_count
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
    """Display a single poet and their ghazals"""
    conn = get_db()
    cur = conn.cursor()

    # Get poet info from poets table
    cur.execute("""
        SELECT id, name, name_urdu, birth_year, death_year
        FROM poets 
        WHERE id = %s
    """, (poet_id,))
    
    poet = cur.fetchone()

    if poet is None:
        cur.close()
        conn.close()
        abort(404)

    # Get all ghazals for this poet - using correct columns
    # Note: Using title_urdu for display, first_line as first couplet
    cur.execute("""
        SELECT 
            id, 
            title_urdu, 
            first_line as first_couplet,
            verse_count
        FROM texts
        WHERE poet_id = %s
        ORDER BY id DESC
    """, (poet_id,))
    
    texts = cur.fetchall()

    # Get first verse for each ghazal from verses table
    for text in texts:
        cur.execute("""
            SELECT misra1_urdu, misra2_urdu
            FROM verses
            WHERE text_id = %s
            ORDER BY couplet_index ASC
            LIMIT 1
        """, (text['id'],))
        
        first_verse = cur.fetchone()
        text['first_verse'] = first_verse

    cur.close()
    conn.close()

    return render_template('poet_detail.html', 
                          poet=poet, 
                          texts=texts,
                          total=len(texts))
