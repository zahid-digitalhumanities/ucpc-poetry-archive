# models/ghazal_model.py
from models.base import get_db_connection
import uuid
import hashlib
from datetime import datetime

def get_db():
    return get_db_connection()

# ==================== STATS ====================
def get_stats():
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM poets")
            poets = cur.fetchone()['count']
            cur.execute("SELECT COUNT(*) FROM texts WHERE form = 'ghazal'")
            texts = cur.fetchone()['count']
            cur.execute("SELECT COUNT(*) FROM verses")
            verses = cur.fetchone()['count']
    return {'total_poets': poets, 'total_ghazals': texts, 'total_verses': verses}

# ==================== POETS ====================
def get_all_poets():
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT p.id, p.name, p.name_urdu, p.birth_year, p.death_year,
                       COUNT(t.id) AS ghazal_count
                FROM poets p
                LEFT JOIN texts t ON t.poet_id = p.id AND t.form = 'ghazal'
                GROUP BY p.id ORDER BY p.name
            """)
            return cur.fetchall()

def get_poet_by_id(poet_id):
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, name, name_urdu, bio_english, bio_urdu, birth_year, death_year
                FROM poets WHERE id = %s
            """, (poet_id,))
            return cur.fetchone()

# ==================== GHAZALS ====================
def fetch_texts_by_poet(poet_id):
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, public_id, title_urdu, title_english, verse_count
                FROM texts WHERE poet_id = %s AND form = 'ghazal' ORDER BY id
            """, (poet_id,))
            return cur.fetchall()

def get_ghazal_with_verses(text_id):
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT t.*, p.name AS poet_name, p.name_urdu AS poet_name_urdu
                FROM texts t JOIN poets p ON t.poet_id = p.id WHERE t.id = %s
            """, (text_id,))
            ghazal = cur.fetchone()
            if ghazal:
                cur.execute("SELECT * FROM verses WHERE text_id = %s ORDER BY couplet_index", (text_id,))
                verses = cur.fetchall()
            else:
                verses = []
            return ghazal, verses

def get_navigation(current_id, poet_id):
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM texts WHERE poet_id = %s AND form = 'ghazal' ORDER BY id", (poet_id,))
            ids = [row['id'] for row in cur.fetchall()]
            if not ids:
                return None, None, 0
            try:
                index = ids.index(current_id)
            except ValueError:
                return None, None, len(ids)
            prev_id = ids[index-1] if index>0 else None
            next_id = ids[index+1] if index<len(ids)-1 else None
            return prev_id, next_id, len(ids)

# ✅ INSERT GHAZAL (matches routes call)
def insert_ghazal(poet_id, book_id, contributor_id, title_urdu, title_english,
                  text_urdu, text_english, content_hash, verse_count):
    public_id = str(uuid.uuid4())[:8]
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO texts
                (public_id, poet_id, source_book_id, title_urdu, title_english,
                 text_urdu, text_english, content_hash, verse_count, form, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 'ghazal', %s)
                RETURNING id
            """, (public_id, poet_id, book_id, title_urdu, title_english,
                  text_urdu, text_english, content_hash, verse_count, datetime.now()))
            conn.commit()
            text_id = cur.fetchone()['id']
            # If contributor_id provided, add to contributions
            if contributor_id:
                cur.execute("""
                    INSERT INTO contributions (text_id, contributor_id, role)
                    VALUES (%s, %s, 'editor')
                """, (text_id, contributor_id))
                conn.commit()
            return text_id

# ✅ INSERT VERSE (matches routes call)
def insert_verse(text_id, couplet_index, m1, m2, m1_en, m2_en):
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO verses
                (text_id, couplet_index, verse_text_urdu_1, verse_text_urdu_2,
                 verse_text_english_1, verse_text_english_2)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (text_id, couplet_index, m1, m2, m1_en, m2_en))
            conn.commit()
            return cur.lastrowid

# ==================== CONTRIBUTORS ====================
def get_all_contributors():
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id, name FROM contributors ORDER BY name")
            return cur.fetchall()

def get_or_create_contributor(name, email=None):
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM contributors WHERE name = %s", (name,))
            row = cur.fetchone()
            if row:
                return row['id']
            # Insert new contributor
            cur.execute("""
                INSERT INTO contributors (name, email) VALUES (%s, %s) RETURNING id
            """, (name, email))
            conn.commit()
            return cur.fetchone()['id']

def add_contribution(text_id, contributor_id, role='editor'):
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO contributions (text_id, contributor_id, role)
                VALUES (%s, %s, %s) ON CONFLICT DO NOTHING
            """, (text_id, contributor_id, role))
            conn.commit()

# ==================== BOOKS ====================
def get_books_by_poet(poet_id):
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id, name, name_urdu FROM books WHERE poet_id = %s ORDER BY name", (poet_id,))
            rows = cur.fetchall()
            # Convert to list of dicts for JSON serialization
            if rows:
                # If using RealDictCursor, rows are already dicts; otherwise convert tuples
                if isinstance(rows[0], dict):
                    return rows
                else:
                    return [{'id': r[0], 'name': r[1], 'name_urdu': r[2]} for r in rows]
            return []

# ==================== DUPLICATE CHECK (by content_hash) ====================
def check_duplicate_ghazal(content_hash):
    """Return (is_duplicate, existing_ghazal_dict_or_None)"""
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, poet_id, title_urdu, title_english
                FROM texts
                WHERE content_hash = %s AND form = 'ghazal'
                LIMIT 1
            """, (content_hash,))
            row = cur.fetchone()
            if row:
                # If using RealDictCursor, row is dict; else convert
                if isinstance(row, dict):
                    return True, row
                else:
                    return True, {'id': row[0], 'poet_id': row[1], 'title_urdu': row[2], 'title_english': row[3]}
            return False, None