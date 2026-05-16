import uuid
import hashlib
import re
from collections import Counter
from models.base import get_db_connection   # changed
from modules.ai_tools import translate_urdu_to_english
from modules.meter import detect_meter

# ==================== NORMALIZATION & TOKENIZATION ====================
def normalize_urdu(text):
    if not text:
        return ""
    replacements = {
        "ي": "ی",
        "ك": "ک",
        "ه": "ہ",
        "ة": "ہ",
        "أ": "ا",
        "إ": "ا",
        "ؤ": "و",
        "ئ": "ی"
    }
    for k, v in replacements.items():
        text = text.replace(k, v)
    return text.strip()

def tokenize_urdu(text):
    return re.findall(r'[\u0600-\u06FF]+', text)

def generate_hash(text):
    normalized = normalize_urdu(text.lower())
    return hashlib.md5(normalized.encode('utf-8')).hexdigest()

# ==================== NORMALIZE GHAZAL (for duplicate check) ====================
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

# ==================== VERSES PARSING ====================
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

# ==================== BULK INSERT (with NLP analysis) ====================
def insert_ghazal_bulk(conn, poet_id, book_id, contributor_id,
                       ghazal_text, title_urdu,
                       content_hash, first_couplet_hash, normalized_text):
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO texts (
                poet_id, book_id, title_urdu,
                content_hash, first_couplet_hash, normalized_text,
                created_at, nlp_version
            )
            VALUES (%s, %s, %s, %s, %s, %s, NOW(), 2)
            RETURNING id
        """, (poet_id, book_id, title_urdu,
              content_hash, first_couplet_hash, normalized_text))
        text_id = cur.fetchone()['id']

        # Insert verses
        lines = [l.strip() for l in ghazal_text.split('\n') if l.strip()]
        for i in range(0, len(lines), 2):
            misra1 = lines[i]
            misra2 = lines[i+1] if i+1 < len(lines) else ""
            cur.execute("""
                INSERT INTO verses (text_id, couplet_index, misra1_urdu, misra2_urdu)
                VALUES (%s, %s, %s, %s)
            """, (text_id, (i//2)+1, misra1, misra2))

        conn.commit()
        return text_id, None
    except Exception as e:
        conn.rollback()
        return None, str(e)
    finally:
        cur.close()

# ==================== ADVANCED NLP FUNCTIONS ====================
def detect_radif_advanced(misras):
    """
    Multi‑length radif detection.
    misras: list of second misra strings (misra2_urdu)
    Returns the most common ending phrase (radif) and confidence.
    """
    endings = []
    for line in misras:
        words = line.split()
        # Try lengths 1 to 4 words from the end
        for i in range(1, min(5, len(words)+1)):
            endings.append(" ".join(words[-i:]))
    if not endings:
        return None, 0.0
    common = Counter(endings).most_common(1)[0]
    confidence = common[1] / len(misras)
    return common[0], confidence

def extract_phonetic_pattern(word):
    """Return last 3 characters (basic phonetic approximation)."""
    return word[-3:] if len(word) >= 3 else word

def detect_qaafiya_advanced(verses, radif):
    """
    Extract qaafiya as the word(s) immediately before radif,
    then derive a phonetic pattern.
    Returns (list of qaafiya words, phonetic pattern string).
    """
    if not radif:
        return [], ""
    qaafiya_set = set()
    for v in verses:
        if not v:
            continue
        # radif must be at the end
        if v.endswith(radif):
            remaining = v[:-len(radif)].strip()
            if remaining:
                words = remaining.split()
                if words:
                    qaafiya_set.add(words[-1])
    qaafiya_list = list(qaafiya_set)
    # Phonetic pattern: most common ending of qaafiya words
    if qaafiya_list:
        patterns = [extract_phonetic_pattern(w) for w in qaafiya_list]
        pattern = Counter(patterns).most_common(1)[0][0] if patterns else ""
    else:
        pattern = ""
    return qaafiya_list, pattern

def is_real_matla(misra1, misra2, radif):
    """True if both misras end with the radif."""
    if not radif:
        return False
    return misra1.endswith(radif) and misra2.endswith(radif)

def detect_maqta(poet_name, verses):
    """
    Check if the poet's name (or takhallus) appears in the last couplet.
    Returns boolean.
    """
    if not poet_name or not verses:
        return False
    # Last couplet's second misra (or whole couplet)
    last_couplet = verses[-1]
    misra2 = last_couplet.get('misra2_urdu', '')
    misra1 = last_couplet.get('misra1_urdu', '')
    # Normalize poet name for comparison
    poet_normalized = normalize_urdu(poet_name)
    text = normalize_urdu(misra1 + " " + misra2)
    return poet_normalized in text

def detect_theme_advanced(text):
    """
    Placeholder for future ML‑based theme detection.
    Currently uses keyword expansion.
    """
    text_lower = text.lower()
    love_keywords = ['عشق', 'محبت', 'دل', 'غم', 'اشک', 'آرزو', 'دیدار', 'فراق', 'وصل']
    spiritual_keywords = ['خدا', 'رب', 'اللہ', 'دعا', 'رحمت', 'عشق حقیقی', 'تصوف']
    politics_keywords = ['سیاست', 'حکومت', 'انصاف', 'آزادی', 'وطن', 'ملت']
    if any(w in text_lower for w in love_keywords):
        return 'love'
    elif any(w in text_lower for w in spiritual_keywords):
        return 'spiritual'
    elif any(w in text_lower for w in politics_keywords):
        return 'politics'
    return 'general'

# ==================== FULL GHAZAL ANALYSIS (UPGRADED with METER) ====================
def analyze_ghazal(conn, text_id):
    """
    Run advanced NLP analysis on a single ghazal, including meter detection.
    """
    cur = conn.cursor()
    try:
        # Fetch all verses and poet name
        cur.execute("""
            SELECT v.couplet_index, v.misra1_urdu, v.misra2_urdu,
                   t.poet_id, p.name AS poet_name
            FROM verses v
            JOIN texts t ON v.text_id = t.id
            JOIN poets p ON t.poet_id = p.id
            WHERE v.text_id = %s
            ORDER BY v.couplet_index
        """, (text_id,))
        rows = cur.fetchall()
        if not rows:
            cur.execute("UPDATE texts SET nlp_processed = TRUE WHERE id = %s", (text_id,))
            conn.commit()
            return

        poet_name = rows[0]['poet_name']
        second_misras = []
        verses_list = []
        for r in rows:
            m2 = r['misra2_urdu'] or ''
            if m2:
                second_misras.append(normalize_urdu(m2))
            verses_list.append({
                'misra1_urdu': r['misra1_urdu'] or '',
                'misra2_urdu': m2
            })

        if not second_misras:
            cur.execute("UPDATE texts SET nlp_processed = TRUE WHERE id = %s", (text_id,))
            conn.commit()
            return

        # Advanced radif detection
        radif, radif_confidence = detect_radif_advanced(second_misras)

        # Advanced qaafiya detection
        qaafiya_list, qaafiya_pattern = detect_qaafiya_advanced(second_misras, radif)

        # Matla validation (only first couplet)
        matla_valid = False
        if rows and radif:
            first_m1 = rows[0]['misra1_urdu'] or ''
            first_m2 = rows[0]['misra2_urdu'] or ''
            matla_valid = is_real_matla(first_m1, first_m2, radif)

        # Maqta detection
        maqta_detected = detect_maqta(poet_name, verses_list)

        # Theme detection (full text)
        full_text = ' '.join([(r['misra1_urdu'] or '') + ' ' + (r['misra2_urdu'] or '') for r in rows])
        theme = detect_theme_advanced(full_text)

        # ==================== METER DETECTION ====================
        meter_pattern, meter_confidence, meter_name = detect_meter(verses_list)

        # Update poetic_features with all fields, including meter
        cur.execute("""
            INSERT INTO poetic_features (
                text_id, radif, qaafiya, theme,
                radif_confidence, qaafiya_pattern, maqta_detected,
                meter_name, meter_pattern, meter_confidence,
                created_at
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
            ON CONFLICT (text_id) DO UPDATE
            SET radif = EXCLUDED.radif,
                qaafiya = EXCLUDED.qaafiya,
                theme = EXCLUDED.theme,
                radif_confidence = EXCLUDED.radif_confidence,
                qaafiya_pattern = EXCLUDED.qaafiya_pattern,
                maqta_detected = EXCLUDED.maqta_detected,
                meter_name = EXCLUDED.meter_name,
                meter_pattern = EXCLUDED.meter_pattern,
                meter_confidence = EXCLUDED.meter_confidence
        """, (text_id, radif, qaafiya_list, theme,
              radif_confidence, qaafiya_pattern, maqta_detected,
              meter_name, meter_pattern, meter_confidence))

        # Mark matla/maqta in verses table
        total = len(rows)
        for idx, r in enumerate(rows):
            is_matla = (idx == 0) and matla_valid
            is_maqta = (idx == total - 1) and maqta_detected
            cur.execute("""
                UPDATE verses
                SET is_matla = %s, is_maqta = %s
                WHERE text_id = %s AND couplet_index = %s
            """, (is_matla, is_maqta, text_id, r['couplet_index']))

        # Mark ghazal as NLP processed and update version
        cur.execute("""
            UPDATE texts
            SET nlp_processed = TRUE, nlp_version = 2
            WHERE id = %s
        """, (text_id,))
        conn.commit()

    except Exception as e:
        print(f"Error analyzing ghazal {text_id}: {e}")
        conn.rollback()
    finally:
        cur.close()

# ==================== BOOKS ====================
def get_books_by_poet(poet_id):
    conn = get_db_connection()  
    try:
        cur = conn.cursor()
        cur.execute("SELECT id, name, name_urdu FROM books WHERE poet_id = %s ORDER BY name", (poet_id,))
        rows = cur.fetchall()
        return [{'id': row[0], 'name': row[1], 'name_urdu': row[2]} for row in rows]
    except Exception as e:
        print(f"Error fetching books: {e}")
        return []
    finally:
        conn.close()