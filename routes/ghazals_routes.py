from flask import Blueprint, render_template, abort, jsonify, redirect, url_for
from models.db import get_db

ghazals_bp = Blueprint('ghazals', __name__)


# =====================================================
# POSTER PAGE (2 couplets only)
# =====================================================

@ghazals_bp.route('/poster/<int:text_id>')
def poster_page(text_id):
    """Generate poster with 2 couplets only"""
    conn = get_db()
    cur = conn.cursor()

    # Update view count
    try:
        cur.execute("UPDATE texts SET views = COALESCE(views, 0) + 1 WHERE id = %s", (text_id,))
        conn.commit()
    except:
        conn.rollback()

    # Get ghazal info
    cur.execute("""
        SELECT t.id, t.verse_count, t.views, t.poet_id,
               p.name as poet_name, p.name_urdu as poet_name_urdu
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
        SELECT misra1_urdu, misra2_urdu, couplet_index
        FROM verses
        WHERE text_id = %s
        ORDER BY couplet_index ASC
    """, (text_id,))
    all_verses = cur.fetchall()

    cur.close()
    conn.close()

    # First 2 couplets for poster
    poster_verses = all_verses[:2]

    return render_template('poster.html', 
                          ghazal=ghazal, 
                          poster_verses=poster_verses)


# =====================================================
# COMPLETE GHAZAL PAGE (All verses)
# =====================================================

@ghazals_bp.route('/ghazal/<int:text_id>')
def ghazal_page(text_id):
    """Display complete ghazal with all verses"""
    conn = get_db()
    cur = conn.cursor()

    # Update view count
    try:
        cur.execute("UPDATE texts SET views = COALESCE(views, 0) + 1 WHERE id = %s", (text_id,))
        conn.commit()
    except:
        conn.rollback()

    # Get ghazal info
    cur.execute("""
        SELECT t.id, t.verse_count, t.views, t.poet_id,
               p.name as poet_name, p.name_urdu as poet_name_urdu
        FROM texts t
        LEFT JOIN poets p ON t.poet_id = p.id
        WHERE t.id = %s
    """, (text_id,))
    ghazal = cur.fetchone()

    if ghazal is None:
        cur.close()
        conn.close()
        abort(404)

    # Get ALL verses
    cur.execute("""
        SELECT misra1_urdu, misra2_urdu, couplet_index
        FROM verses
        WHERE text_id = %s
        ORDER BY couplet_index ASC
    """, (text_id,))
    verses = cur.fetchall()

    cur.close()
    conn.close()

    return render_template('ghazal.html', ghazal=ghazal, verses=verses)


# =====================================================
# BACKWARD COMPATIBILITY (Redirect old URLs)
# =====================================================

@ghazals_bp.route('/view/<int:text_id>')
def view_redirect(text_id):
    """Redirect old /view/ URLs to poster page"""
    return redirect(url_for('ghazals.poster_page', text_id=text_id))


@ghazals_bp.route('/full/<int:text_id>')
def full_redirect(text_id):
    """Redirect old /full/ URLs to ghazal page"""
    return redirect(url_for('ghazals.ghazal_page', text_id=text_id))


# =====================================================
# RANDOM GHAZAL API
# =====================================================

@ghazals_bp.route('/api/random-ghazal')
def random_ghazal():
    """Return random ghazal ID"""
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