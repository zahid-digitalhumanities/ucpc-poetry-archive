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
            rows = cur.fetchall()
            return [dict(row) for row in rows]

def get_poet_by_id(poet_id):
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, name, name_urdu, bio_english, bio_urdu, 
                       birth_year, death_year, wikipedia_url
                FROM poets WHERE id = %s
            """, (poet_id,))
            row = cur.fetchone()
            if not row:
                return None
            poet = dict(row)
            poet['biography'] = poet.get('bio_english', '')
            return poet

# ==================== GHAZALS ====================
def fetch_texts_by_poet(poet_id):
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, public_id, title_urdu, title_english, verse_count
                FROM texts WHERE poet_id = %s AND form = 'ghazal' ORDER BY id
            """, (poet_id,))
            texts = cur.fetchall()
            result = []
            for text in texts:
                text_dict = dict(text)
                cur.execute("""
                    SELECT misra1_urdu, misra2_urdu
                    FROM verses
                    WHERE text_id = %s
                    ORDER BY couplet_index ASC
                    LIMIT 2
                """, (text_dict['id'],))
                verses = cur.fetchall()
                first_verse = None
                second_verse = None
                if len(verses) >= 1:
                    first_verse = {'misra1_urdu': verses[0]['misra1_urdu'] or '', 'misra2_urdu': verses[0]['misra2_urdu'] or ''}
                if len(verses) >= 2:
                    second_verse = {'misra1_urdu': verses[1]['misra1_urdu'] or '', 'misra2_urdu': verses[1]['misra2_urdu'] or ''}
                text_dict['first_verse'] = first_verse
                text_dict['second_verse'] = second_verse
                result.append(text_dict)
            return result

# ✅ FIXED: get_ghazal_with_verses with debug prints
def get_ghazal_with_verses(text_id):
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            # Fetch ghazal
            cur.execute("""
                SELECT t.id, t.title_urdu, t.title_english, t.poet_id, t.verse_count, t.text_urdu,
                       p.name AS poet_name, p.name_urdu AS poet_name_urdu
                FROM texts t
                JOIN poets p ON t.poet_id = p.id
                WHERE t.id = %s
            """, (text_id,))
            ghazal_row = cur.fetchone()
            if not ghazal_row:
                print(f"DEBUG: No ghazal found for text_id {text_id}")
                return None, []

            ghazal = dict(ghazal_row)
            print(f"DEBUG: Ghazal fetched, poet={ghazal.get('poet_name')}")

            # Fetch verses
            cur.execute("""
                SELECT couplet_index, misra1_urdu, misra2_urdu
                FROM verses
                WHERE text_id = %s
                ORDER BY couplet_index
            """, (text_id,))
            rows = cur.fetchall()
            print(f"DEBUG: Found {len(rows)} verse rows for text_id {text_id}")
            if rows:
                print(f"DEBUG: First row columns: {rows[0].keys()}")
                print(f"DEBUG: First misra1_urdu sample: {rows[0].get('misra1_urdu', '')[:50]}")
            verses = []
            for row in rows:
                verses.append({
                    'misra1_urdu': row.get('misra1_urdu', ''),
                    'misra2_urdu': row.get('misra2_urdu', ''),
                    'misra1_english': '',
                    'misra2_english': ''
                })
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

# ==================== INSERT GHAZAL & VERSE ====================
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
            if contributor_id:
                cur.execute("""
                    INSERT INTO contributions (text_id, contributor_id, role)
                    VALUES (%s, %s, 'editor')
                """, (text_id, contributor_id))
                conn.commit()
            return text_id

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
            return [dict(row) for row in cur.fetchall()]

def get_or_create_contributor(name, email=None):
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM contributors WHERE name = %s", (name,))
            row = cur.fetchone()
            if row:
                return row['id']
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
            return [dict(row) for row in rows]

# ==================== DUPLICATE CHECK ====================
def check_duplicate_ghazal(content_hash):
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
                return True, dict(row)
            return False, None

# ==================== RECENT GHAZALS ====================
def get_recent_ghazals(limit=10):
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT t.id, t.title_english, t.title_urdu, p.name as poet_name
                FROM texts t
                JOIN poets p ON t.poet_id = p.id
                WHERE t.form = 'ghazal'
                ORDER BY t.created_at DESC
                LIMIT %s
            """, (limit,))
            rows = cur.fetchall()
            return [dict(row) for row in rows]
