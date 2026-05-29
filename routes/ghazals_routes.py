from flask import Blueprint, render_template, abort
from models.db import get_db

ghazals_bp = Blueprint('ghazals', name)

=====================================================

FULL GHAZAL PAGE

=====================================================

@ghazals_bp.route('/ghazal/"int:text_id" (int:text_id)')
def full_ghazal(text_id):

conn = get_db()
cur = conn.cursor()

# GET GHAZAL INFO
cur.execute("""
    SELECT
        t.id,
        t.verse_count,
        t.poet_id,
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

# GET ALL VERSES
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

# VISITOR COUNTER
cur.execute("""
    UPDATE texts
    SET views = COALESCE(views, 0) + 1
    WHERE id = %s
""", (text_id,))

conn.commit()

# GET UPDATED COUNT
cur.execute("""
    SELECT views
    FROM texts
    WHERE id = %s
""", (text_id,))

views_result = cur.fetchone()

total_views = views_result[0] if views_result else 0

cur.close()
conn.close()

return render_template(
    'full_ghazal.html',
    ghazal=ghazal,
    all_verses=all_verses,
    total_views=total_views
)

=====================================================

POSTER GENERATOR PAGE

=====================================================

@ghazals_bp.route('/poster/"int:text_id" (int:text_id)')
def poster_view(text_id):

conn = get_db()
cur = conn.cursor()

# GET GHAZAL INFO
cur.execute("""
    SELECT
        t.id,
        t.verse_count,
        t.poet_id,
        p.name as poet_name,
        p.name_urdu as poet_name_urdu,
        COALESCE(t.views, 0) as views
    FROM texts t
    LEFT JOIN poets p ON t.poet_id = p.id
    WHERE t.id = %s
""", (text_id,))

ghazal = cur.fetchone()

if ghazal is None:
    cur.close()
    conn.close()
    abort(404)

# GET VERSES
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

# FIRST 2 COUPLETS FOR POSTER
poster_verses = all_verses[:2]

return render_template(
    'view.html',
    ghazal=ghazal,
    poster_verses=poster_verses,
    all_verses=all_verses
)