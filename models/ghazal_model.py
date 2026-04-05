import uuid
import hashlib
from models.base import get_db_connection

def get_db():
    return get_db_connection()

# ✅ FIXED stats
def get_stats():
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM poets")
            poets = cur.fetchone()['count']

            cur.execute("SELECT COUNT(*) FROM texts WHERE form = 'ghazal'")
            texts = cur.fetchone()['count']

            cur.execute("SELECT COUNT(*) FROM verses")
            verses = cur.fetchone()['count']

    return {
        'total_poets': poets,
        'total_ghazals': texts,
        'total_verses': verses
    }

# ✅ All poets
def get_all_poets():
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT p.id, p.name, p.name_urdu, p.birth_year, p.death_year,
                       COUNT(t.id) AS ghazal_count
                FROM poets p
                LEFT JOIN texts t ON t.poet_id = p.id AND t.form = 'ghazal'
                GROUP BY p.id
                ORDER BY p.name
            """)
            return cur.fetchall()

# ✅ Single poet
def get_poet_by_id(poet_id):
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, name, name_urdu, bio_english, bio_urdu, birth_year, death_year
                FROM poets
                WHERE id = %s
            """, (poet_id,))
            return cur.fetchone()

# ✅ Ghazals list by poet
def fetch_texts_by_poet(poet_id):
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, public_id, title_urdu, title_english, verse_count
                FROM texts
                WHERE poet_id = %s AND form = 'ghazal'
                ORDER BY id
            """, (poet_id,))
            return cur.fetchall()

# ✅ Full ghazal + verses
def get_ghazal_with_verses(text_id):
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT t.*, p.name AS poet_name, p.name_urdu AS poet_name_urdu
                FROM texts t
                JOIN poets p ON t.poet_id = p.id
                WHERE t.id = %s
            """, (text_id,))
            ghazal = cur.fetchone()

            if ghazal:
                cur.execute("""
                    SELECT *
                    FROM verses
                    WHERE text_id = %s
                    ORDER BY couplet_index
                """, (text_id,))
                verses = cur.fetchall()
            else:
                verses = []

            return ghazal, verses

# ✅ Navigation
def get_navigation(current_id, poet_id):
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id
                FROM texts
                WHERE poet_id = %s AND form = 'ghazal'
                ORDER BY id
            """, (poet_id,))
            ids = [row['id'] for row in cur.fetchall()]

            if not ids:
                return None, None, 0

            try:
                index = ids.index(current_id)
            except ValueError:
                return None, None, len(ids)

            prev_id = ids[index - 1] if index > 0 else None
            next_id = ids[index + 1] if index < len(ids) - 1 else None

            return prev_id, next_id, len(ids)

# ✅ Contributors
def get_all_contributors():
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id, name FROM contributors ORDER BY name")
            return cur.fetchall()

# ✅ Books
def get_books_by_poet(poet_id):
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, name, name_urdu
                FROM books
                WHERE poet_id = %s
                ORDER BY name
            """, (poet_id,))
            return cur.fetchall()
