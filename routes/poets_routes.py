from flask import Blueprint, render_template
from models.db import get_db

poets_bp = Blueprint("poets", __name__)


@poets_bp.route("/")
def poets():
    """Display all poets with ghazal count"""
    conn = get_db()
    cur = conn.cursor()

    # Get poets with their ghazal count
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

    return render_template("poets.html", poets=poets)


@poets_bp.route("/<int:poet_id>")
def poet_detail(poet_id):
    """Display poet details and their ghazals"""
    conn = get_db()
    cur = conn.cursor()

    # Get poet information
    cur.execute("""
        SELECT id, name, name_urdu, birth_year, death_year, bio
        FROM poets 
        WHERE id = %s
    """, (poet_id,))
    
    poet = cur.fetchone()

    if not poet:
        cur.close()
        conn.close()
        return "Poet not found", 404

    # Get all ghazals for this poet
    cur.execute("""
        SELECT 
            id, 
            poet_name, 
            title, 
            first_couplet, 
            verse_count
        FROM texts
        WHERE poet_id = %s
        ORDER BY id DESC
    """, (poet_id,))
    
    texts = cur.fetchall()

    cur.close()
    conn.close()

    return render_template("poet_detail.html", poet=poet, texts=texts)
