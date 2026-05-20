from flask import Blueprint
from flask import render_template

from models.db import get_db

poets_bp = Blueprint(
    "poets",
    __name__
)

# =====================================================
# ALL POETS
# =====================================================

@poets_bp.route("/")
def poets():

    conn = get_db()

    cur = conn.cursor()

    cur.execute("""

        SELECT
            id,
            name,
            name_urdu
        FROM poets
        ORDER BY name ASC

    """)

    poets = cur.fetchall()

    cur.close()
    conn.close()

    return render_template(
        "poets.html",
        poets=poets
    )

# =====================================================
# POET DETAIL
# =====================================================

@poets_bp.route("/<int:poet_id>")
def poet_detail(poet_id):

    conn = get_db()

    cur = conn.cursor()

    cur.execute("""

        SELECT *
        FROM poets
        WHERE id = %s

    """, (poet_id,))

    poet = cur.fetchone()

    cur.execute("""

        SELECT
            id,
            poet_name,
            first_couplet,
            verse_count
        FROM texts
        WHERE poet_id = %s
        ORDER BY id DESC

    """, (poet_id,))

    texts = cur.fetchall()

    cur.close()
    conn.close()

    return render_template(
        "poet_detail.html",
        poet=poet,
        texts=texts
    )