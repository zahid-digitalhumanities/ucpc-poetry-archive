import psycopg2
import psycopg2.extras
import uuid
import hashlib
from config import DB_CONFIG

def get_db():
    return psycopg2.connect(
        dbname=DB_CONFIG['dbname'],
        user=DB_CONFIG['user'],
        password=DB_CONFIG['password'],
        host=DB_CONFIG['host'],
        port=DB_CONFIG['port'],
        cursor_factory=psycopg2.extras.RealDictCursor
    )
def get_stats():
    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM poets")
        poets = cur.fetchone()['count']
        cur.execute("SELECT COUNT(*) FROM texts WHERE form = 'ghazal'")
        texts = cur.fetchone()['count']
        cur.execute("SELECT COUNT(*) FROM verses")
        verses = cur.fetchone()['count']
        return {'total_poets': poets, 'total_ghazals': texts, 'texts': texts, 'total_verses': verses, 'verses': verses}
    except Exception as e:
        print("ERROR get_stats:", e)
        return {'total_poets': 0, 'total_ghazals': 0, 'texts': 0, 'total_verses': 0, 'verses': 0}
    finally:
        conn.close()

def get_all_poets():
    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT p.id, p.name, p.name_urdu, p.birth_year, p.death_year,
                   COUNT(t.id) AS ghazal_count
            FROM poets p
            LEFT JOIN texts t ON t.poet_id = p.id AND t.form = 'ghazal'
            GROUP BY p.id
            ORDER BY p.name
        """)
        return cur.fetchall()
    except Exception as e:
        print("ERROR get_all_poets:", e)
        return []
    finally:
        conn.close()

def get_poet_by_id(poet_id):
    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT id, name, name_urdu, bio_english, bio_urdu,
                   birth_year, death_year
            FROM poets WHERE id = %s
        """, (poet_id,))
        return cur.fetchone()
    except Exception as e:
        print("ERROR get_poet_by_id:", e)
        return None
    finally:
        conn.close()

def fetch_texts_by_poet(poet_id):
    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT id, public_id, title_urdu, title_english, verse_count
            FROM texts
            WHERE poet_id = %s AND form = 'ghazal'
            ORDER BY id
        """, (poet_id,))
        return cur.fetchall()
    except Exception as e:
        print("ERROR fetch_texts_by_poet:", e)
        return []
    finally:
        conn.close()

def get_ghazals_by_poet(poet_id):
    return fetch_texts_by_poet(poet_id)

def get_ghazal_with_verses(text_id):
    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT t.*,
                   p.name AS poet_name,
                   p.name_urdu AS poet_name_urdu
            FROM texts t
            JOIN poets p ON t.poet_id = p.id
            WHERE t.id = %s
        """, (text_id,))
        ghazal = cur.fetchone()
        if ghazal:
            cur.execute("""
                SELECT * FROM verses
                WHERE text_id = %s
                ORDER BY couplet_index
            """, (text_id,))
            verses = cur.fetchall()
        else:
            verses = []
        return ghazal, verses
    except Exception as e:
        print("ERROR get_ghazal_with_verses:", e)
        return None, []
    finally:
        conn.close()
def get_navigation(current_id, poet_id):
    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute("SELECT id FROM texts WHERE poet_id = %s AND form = 'ghazal' ORDER BY id", (poet_id,))
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
    except Exception as e:
        print("ERROR get_navigation:", e)
        return None, None, 0
    finally:
        conn.close()

def get_all_contributors():
    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute("SELECT id, name FROM contributors ORDER BY name")
        return cur.fetchall()
    except Exception as e:
        print("ERROR get_all_contributors:", e)
        return []
    finally:
        conn.close()

def get_books_by_poet(poet_id):
    """Return list of books for a given poet."""
    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute("SELECT id, name, name_urdu FROM books WHERE poet_id = %s ORDER BY name", (poet_id,))
        return cur.fetchall()
    except Exception as e:
        print("ERROR get_books_by_poet:", e)
        return []
    finally:
        conn.close()

def check_duplicate_ghazal(content_hash):
    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT t.id, t.title_urdu, t.title_english,
                   p.name as poet_name, p.name_urdu as poet_name_urdu, p.id as poet_id
            FROM texts t
            JOIN poets p ON t.poet_id = p.id
            WHERE t.content_hash = %s AND t.form IN ('ghazal', 'nazm')
        """, (content_hash,))
        existing = cur.fetchone()
        if existing:
            return True, existing
        return False, None
    except Exception as e:
        print("ERROR check_duplicate_ghazal:", e)
        return False, None
    finally:
        conn.close()

def get_or_create_contributor(name, email):
    if not name:
        return None
    conn = get_db()
    try:
        cur = conn.cursor()
        if email:
            cur.execute("SELECT id FROM contributors WHERE name = %s AND email = %s", (name, email))
        else:
            cur.execute("SELECT id FROM contributors WHERE name = %s", (name,))
        row = cur.fetchone()
        if row:
            return row['id']
        cur.execute("INSERT INTO contributors (name, email) VALUES (%s, %s) RETURNING id", (name, email))
        conn.commit()
        return cur.fetchone()['id']
    except Exception as e:
        print("ERROR get_or_create_contributor:", e)
        return None
    finally:
        conn.close()

def insert_ghazal(poet_id, book_id, contributor_id, title_urdu, title_english,
                  text_urdu, text_english, content_hash, verse_count):
    conn = get_db()
    try:
        cur = conn.cursor()
        public_id = str(uuid.uuid4())[:8]
        cur.execute("""
            INSERT INTO texts (public_id, poet_id, book_id, contributor_id,
                               title_urdu, title_english, text_urdu, text_english,
                               content_hash, verse_count, form, language)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (public_id, poet_id, book_id, contributor_id,
              title_urdu, title_english, text_urdu, text_english,
              content_hash, verse_count, 'ghazal', 'ur'))
        text_id = cur.fetchone()['id']
        conn.commit()
        return text_id
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def insert_verse(text_id, couplet_index, misra1_urdu, misra2_urdu, misra1_english, misra2_english):
    conn = get_db()
    try:
        cur = conn.cursor()
        search_text = f"{misra1_urdu} {misra2_urdu}" if misra2_urdu else misra1_urdu
        cur.execute("""
            INSERT INTO verses (text_id, couplet_index,
                                misra1_urdu, misra2_urdu,
                                misra1_english, misra2_english,
                                search_text, verse_count)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (text_id, couplet_index,
              misra1_urdu, misra2_urdu,
              misra1_english, misra2_english,
              search_text, 1))  # verse_count in verses table may be per verse, not total
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()