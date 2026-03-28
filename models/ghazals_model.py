from models.base import get_db

def fetch_texts_by_poet(poet_id):
    """Return all texts (ghazals and nazms) for a poet, with titles and verse counts."""
    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT id, title_urdu, title_english, verse_count
            FROM texts
            WHERE poet_id = %s AND form IN ('ghazal', 'nazm')
            ORDER BY id DESC
        """, (poet_id,))
        return cur.fetchall()
    finally:
        cur.close()
        conn.close()

def fetch_ghazal_detail(text_id):
    """Fetch details of a single text (works for ghazal or nazm)."""
    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT t.*, p.name AS poet_name, p.name_urdu AS poet_name_urdu
            FROM texts t
            JOIN poets p ON t.poet_id = p.id
            WHERE t.id = %s
        """, (text_id,))
        text = cur.fetchone()

        cur.execute("""
            SELECT misra1_urdu, misra2_urdu,
                   misra1_english, misra2_english,
                   couplet_index
            FROM verses
            WHERE text_id = %s
            ORDER BY couplet_index
        """, (text_id,))
        verses = cur.fetchall()

        return text, verses
    finally:
        cur.close()
        conn.close()

def get_navigation(current_id, poet_id):
    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT id FROM texts
            WHERE poet_id = %s AND form IN ('ghazal', 'nazm')
            ORDER BY id
        """, (poet_id,))
        ids = [row['id'] for row in cur.fetchall()]
        if not ids:
            return None, None, 0
        try:
            index = ids.index(current_id)
        except ValueError:
            return None, None, len(ids)
        prev_id = ids[index-1] if index > 0 else None
        next_id = ids[index+1] if index < len(ids)-1 else None
        return prev_id, next_id, len(ids)
    finally:
        cur.close()
        conn.close()