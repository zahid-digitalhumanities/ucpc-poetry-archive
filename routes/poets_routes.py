from flask import Blueprint, render_template
from models.db import get_db

poets_bp = Blueprint("poets", __name__)

@poets_bp.route("/")
def poets():
    conn = get_db()
    cur = conn.cursor()

    # Get poets with ghazal count
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
