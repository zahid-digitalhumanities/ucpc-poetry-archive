from flask import Blueprint, render_template, abort
from models.db import get_db

poets_bp = Blueprint("poets", __name__)


@poets_bp.route("/")
def poets():
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

    return render_template("poets.html", poets=poets)


@poets_bp.route("/<int:poet_id>")
def poet_detail(poet_id):
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT id, name, name_urdu
        FROM poets 
        WHERE id = %s
    """, (poet_id,))
    
    poet = cur.fetchone()

    if poet is None:
        cur.close()
        conn.close()
        abort(404)

    cur.execute("""
        SELECT id, poet_name, first_couplet, verse_count
        FROM texts
        WHERE poet_id = %s
        ORDER BY id DESC
    """, (poet_id,))
    
    texts = cur.fetchall()

    cur.close()
    conn.close()

    return render_template("poet_detail.html", poet=poet, texts=texts)
