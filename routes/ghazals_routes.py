from flask import Blueprint, render_template, abort
from models.db import get_db

ghazals_bp = Blueprint('ghazals', __name__)


# =========================================
# POSTER / REEL GENERATOR PAGE
# =========================================
@ghazals_bp.route('/view/<int:text_id>')
def view_ghazal(text_id):
    """
    Page for generating posters (1080x1920 for Reels)
    Shows: poster, download button, themes, dedication fields
    Only shows FIRST 2 couplets
    """
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            t.id,
            t.title,
            t.poet_id,
            p.name AS poet_name,
            p.name_urdu AS poet_name_urdu
        FROM texts t
        LEFT JOIN poets p
        ON t.poet_id = p.id
        WHERE t.id = %s
    """, (text_id,))

    ghazal = cur.fetchone()

    if not ghazal:
        cur.close()
        conn.close()
        abort(404)

    cur.execute("""
        SELECT
            misra1_urdu,
            misra2_urdu,
            couplet_index
        FROM verses
        WHERE text_id = %s
        ORDER BY couplet_index ASC
    """, (text_id,))

    all_verses = cur.fetchall()

    cur.close()
    conn.close()

    # ONLY FIRST 2 COUPLETS FOR POSTER (Reel format)
    poster_verses = all_verses[:2]

    return render_template(
        'view.html',
        ghazal=ghazal,
        poster_verses=poster_verses
    )


# =========================================
# FULL GHAZAL READING PAGE
# =========================================
@ghazals_bp.route('/ghazal/<int:text_id>')
def read_full_ghazal(text_id):
    """
    Page for reading COMPLETE ghazal
    Shows: ALL couplets, clean reading interface
    NO poster generator, NO download button
    Used for Facebook sharing
    """
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            t.id,
            t.title,
            t.poet_id,
            p.name AS poet_name,
            p.name_urdu AS poet_name_urdu
        FROM texts t
        LEFT JOIN poets p
        ON t.poet_id = p.id
        WHERE t.id = %s
    """, (text_id,))

    ghazal = cur.fetchone()

    if not ghazal:
        cur.close()
        conn.close()
        abort(404)

    cur.execute("""
        SELECT
            misra1_urdu,
            misra2_urdu,
            couplet_index
        FROM verses
        WHERE text_id = %s
        ORDER BY couplet_index ASC
    """, (text_id,))

    all_verses = cur.fetchall()

    cur.close()
    conn.close()

    return render_template(
        'ghazal_read.html',
        ghazal=ghazal,
        all_verses=all_verses
    )