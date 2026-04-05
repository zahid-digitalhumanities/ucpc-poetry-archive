# bulk_model.py
import uuid
import hashlib
import re
from models.ghazal_model import get_db
from modules.ai_tools import translate_urdu_to_english

def normalize_ghazal(text):
    text = text.strip()
    text = re.sub(r'\s+', ' ', text)
    text = text.replace('،', '').replace('.', '').replace('!', '')
    return text.lower()

def is_duplicate(conn, ghazal_text):
    normalized = normalize_ghazal(ghazal_text)
    content_hash = hashlib.sha256(normalized.encode('utf-8')).hexdigest()
    cur = conn.cursor()
    cur.execute("SELECT id, title_urdu, poet_id FROM texts WHERE content_hash = %s", (content_hash,))
    result = cur.fetchone()
    cur.close()
    if result:
        return True, result['id'], result['title_urdu'], result['poet_id']
    return False, None, None, None

def split_misra_pairs(lines):
    pairs = []
    for i in range(0, len(lines)-1, 2):
        pairs.append((lines[i], lines[i+1]))
    return pairs

def get_or_create_contributor(conn, name, email=None):
    if not name:
        return None
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

def insert_ghazal_bulk(conn, poet_id, book_id, contributor_id, ghazal_text, title_urdu=None):
    cur = conn.cursor()
    try:
        lines = [l.strip() for l in ghazal_text.split('\n') if l.strip()]
        if len(lines) < 2:
            return None, "Not enough lines"
        pairs = split_misra_pairs(lines)
        if not pairs:
            return None, "Could not split into misra pairs"
        if title_urdu is None:
            title_urdu = pairs[0][0]
        title_en_raw = translate_urdu_to_english(title_urdu)
        title_en = title_en_raw.strip() if title_en_raw else "[Translation unavailable]"
        normalized = normalize_ghazal(ghazal_text)
        content_hash = hashlib.sha256(normalized.encode('utf-8')).hexdigest()
        public_id = str(uuid.uuid4())[:8]
        cur.execute("""
            INSERT INTO texts (public_id, poet_id, book_id, contributor_id,
                               title_urdu, title_english,
                               text_urdu, text_english,
                               verse_count, content_hash, form, language)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (public_id, poet_id, book_id, contributor_id,
              title_urdu, title_en,
              ghazal_text, "",
              len(pairs), content_hash, 'ghazal', 'ur'))
        text_id = cur.fetchone()['id']
        for i, (m1, m2) in enumerate(pairs, 1):
            m1_en = translate_urdu_to_english(m1) or "[Translation unavailable]"
            m2_en = translate_urdu_to_english(m2) if m2 else ""
            if m2_en:
                m2_en = m2_en.strip() or "[Translation unavailable]"
            cur.execute("""
                INSERT INTO verses (
                    text_id, couplet_index,
                    misra1_urdu, misra2_urdu,
                    misra1_english, misra2_english,
                    search_text, verse_count
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (text_id, i, m1, m2, m1_en, m2_en, f"{m1} {m2}" if m2 else m1, len(pairs)))
        conn.commit()
        return text_id, None
    except Exception as e:
        conn.rollback()
        return None, str(e)
    finally:
        cur.close()

def get_books_by_poet(poet_id):
    """Return list of books for a given poet."""
    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute("SELECT id, name, name_urdu FROM books WHERE poet_id = %s ORDER BY name", (poet_id,))
        return cur.fetchall()
    except Exception as e:
        print(f"Error fetching books: {e}")
        return []
    finally:
        conn.close()