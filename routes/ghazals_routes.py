from flask import Blueprint, render_template, abort
from models.db import get_db

ghazals_bp = Blueprint("ghazals", __name__)


@ghazals_bp.route("/view/<int:text_id>")
def view_ghazal(text_id):
    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT * FROM texts WHERE id = %s", (text_id,))
    ghazal = cur.fetchone()

    if ghazal is None:
        cur.close()
        conn.close()
        abort(404)

    cur.execute("""
        SELECT * FROM verses 
        WHERE text_id = %s 
        ORDER BY verse_number ASC
    """, (text_id,))
    
    verses = cur.fetchall()

    cur.close()
    conn.close()

    return render_template("view.html", ghazal=ghazal, verses=verses)
