from flask import Blueprint, render_template, abort, jsonify
from models.db import get_db

ghazals_bp = Blueprint('ghazals', __name__)


# =====================================================
# MAIN VIEW ROUTE (Poster Page)
# =====================================================

@ghazals_bp.route('/view/<int:text_id>')
@ghazals_bp.route('/ghazal/<int:text_id>')
def view_ghazal(text_id):
    """Display poster page with 2 couplets only"""
    conn = get_db()
    cur = conn.cursor()

    # Increase visitor count
    try:
        cur.execute("""
            UPDATE texts
            SET views = COALESCE(views, 0) + 1
            WHERE id = %s
        """, (text_id,))
        conn.commit()
    except Exception:
        conn.rollback()

    # Get ghazal info
    cur.execute("""
        SELECT
            t.id,
            t.verse_count,
            t.poet_id,
            t.views,
            p.name as poet_name,
            p.name_urdu as poet_name_urdu
        FROM texts t
        LEFT JOIN poets p ON t.poet_id = p.id
        WHERE t.id = %s
    """, (text_id,))

    ghazal = cur.fetchone()

    if ghazal is None:
        cur.close()
        conn.close()
        abort(404)

    # Get all verses
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

    # First 2 couplets for poster (4 misra)
    poster_verses = all_verses[:2]

    return render_template(
        'view.html',
        ghazal=ghazal,
        poster_verses=poster_verses,
        all_verses=all_verses
    )


# =====================================================
# COMPLETE GHAZAL PAGE (Full Reading)
# =====================================================

@ghazals_bp.route('/ghazal/<int:text_id>/full')
def full_ghazal(text_id):
    """Display complete ghazal for reading (all verses)"""
    conn = get_db()
    cur = conn.cursor()

    # Increase visitor count
    try:
        cur.execute("""
            UPDATE texts
            SET views = COALESCE(views, 0) + 1
            WHERE id = %s
        """, (text_id,))
        conn.commit()
    except Exception:
        conn.rollback()

    # Get ghazal info
    cur.execute("""
        SELECT
            t.id,
            t.verse_count,
            t.poet_id,
            t.views,
            p.name as poet_name,
            p.name_urdu as poet_name_urdu
        FROM texts t
        LEFT JOIN poets p ON t.poet_id = p.id
        WHERE t.id = %s
    """, (text_id,))

    ghazal = cur.fetchone()

    if ghazal is None:
        cur.close()
        conn.close()
        abort(404)

    # Get ALL verses for full reading
    cur.execute("""
        SELECT
            misra1_urdu,
            misra2_urdu,
            couplet_index
        FROM verses
        WHERE text_id = %s
        ORDER BY couplet_index ASC
    """, (text_id,))

    verses = cur.fetchall()

    cur.close()
    conn.close()

    return render_template(
        'full_ghazal.html',
        ghazal=ghazal,
        verses=verses
    )


# =====================================================
# RANDOM GHAZAL API
# =====================================================

@ghazals_bp.route('/api/random-ghazal')
def random_ghazal():
    """Return random ghazal ID for random button"""
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT id FROM texts ORDER BY RANDOM() LIMIT 1")
    result = cur.fetchone()
    cur.close()
    conn.close()

    if result:
        return jsonify({"id": result["id"]})
    else:
        return jsonify({"error": "No ghazals found"}), 404