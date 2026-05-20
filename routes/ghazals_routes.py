from flask import Blueprint
from flask import render_template

from models.db import get_db

ghazals_bp = Blueprint(
    "ghazals",
    __name__
)

# =====================================================
# VIEW GHAZAL
# =====================================================

@ghazals_bp.route("/view/<int:text_id>")
def view_ghazal(text_id):

    conn = get_db()

    cur = conn.cursor()

    cur.execute("""

        SELECT *
        FROM texts
        WHERE id = %s

    """, (text_id,))

    ghazal = cur.fetchone()

    cur.execute("""

        SELECT *
        FROM verses
        WHERE text_id = %s
        ORDER BY verse_number ASC

    """, (text_id,))

    verses = cur.fetchall()

    cur.close()
    conn.close()

    return render_template(
        "view.html",
        ghazal=ghazal,
        verses=verses
    )