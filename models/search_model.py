# models/search_model.py
import re
import json
import numpy as np

# =========================================================
# GRACEFUL RAPIDFUZZ FALLBACK (CRITICAL FOR RENDER DEPLOYMENT)
# =========================================================
try:
    from rapidfuzz import fuzz
    RAPIDFUZZ_AVAILABLE = True
except ImportError:
    fuzz = None
    RAPIDFUZZ_AVAILABLE = False
    print("⚠️ rapidfuzz not installed - fuzzy search will use basic matching")

from models.base import get_db_connection
from modules.embeddings import generate_embedding

# =========================================================
# ROMAN ENGINE
# =========================================================
try:
    from modules.roman_engine.matcher import process_query
except ImportError:
    def process_query(x):
        return x

# =========================================================
# HELPER FUNCTION FOR FUZZY MATCHING (with fallback)
# =========================================================
def fuzzy_ratio(s1, s2):
    """Safe fuzzy ratio that works with or without rapidfuzz"""
    if not s1 or not s2:
        return 0.0
    if RAPIDFUZZ_AVAILABLE and fuzz:
        try:
            return fuzz.ratio(s1, s2) / 100.0
        except:
            return 1.0 if s1.lower() == s2.lower() else 0.0
    else:
        # Basic fallback - exact match or substring
        s1_lower = s1.lower()
        s2_lower = s2.lower()
        if s1_lower == s2_lower:
            return 1.0
        if s1_lower in s2_lower or s2_lower in s1_lower:
            return 0.7
        return 0.0

# =========================================================
# ROMAN → URDU DICTIONARY (keep your full dictionary)
# =========================================================
ROMAN_DICT = {
    "mohabbat": "محبت",
    "ishq": "عشق",
    "pyar": "پیار",
    "dard": "درد",
    "zindagi": "زندگی",
    "raat": "رات",
    "tanhaai": "تنہائی",
    "yaad": "یاد",
    "dil": "دل",
    "aankh": "آنکھ",
    "lab": "لب",
    "chehra": "چہرہ",
    "husn": "حسن",
    "khuda": "خدا",
    "safar": "سفر",
    "manzil": "منزل",
    "dunya": "دنیا",
    "gham": "غم",
    "aansu": "آنسو",
    "jaan": "جان",
    "night": "رات",
    "love": "محبت",
    "lonely": "تنہائی",
    "sad": "غم",
    "heart": "دل",
    "life": "زندگی",
    "death": "موت",
    "moon": "چاند",
    "flower": "پھول",
    "pain": "درد",
    "hope": "امید",
    "waiting": "انتظار",

    # Numbers 1–20
    "ek": "ایک",
    "do": "دو",
    "teen": "تین",
    "chaar": "چار",
    "paanch": "پانچ",
    "chhe": "چھے",
    "saat": "سات",
    "aath": "آٹھ",
    "nau": "نو",
    "das": "دس",
    "gyaarah": "گیارہ",
    "baarah": "بارہ",
    "terah": "تیرہ",
    "chaudah": "چودہ",
    "pandrah": "پندرہ",
    "solah": "سولہ",
    "satrah": "سترہ",
    "athaarah": "اٹھارہ",
    "unnis": "انیس",
    "bees": "بیس",

    # Days
    "itwaar": "اتوار",
    "peer": "پیر",
    "mangal": "منگل",
    "budh": "بدھ",
    "jumerat": "جمعرات",
    "jummah": "جمعہ",
    "hafta": "ہفتہ",

    # Months
    "muharram": "محرم",
    "safar_month": "صفر",
    "rabiul_awwal": "ربیع الاول",
    "rabiul_saani": "ربیع الثانی",
    "jamadiul_awwal": "جمادی الاول",
    "jamadiul_saani": "جمادی الثانی",
    "rajab": "رجب",
    "shabaan": "شعبان",
    "ramadan": "رمضان",
    "shawwal": "شوال",
    "zilqadah": "ذوالقعدہ",
    "zilhijjah": "ذوالحجہ",
    "janvari": "جنوری",
    "farvari": "فروری",
    "march": "مارچ",
    "april": "اپریل",
    "may": "مئی",
    "june": "جون",
    "july": "جولائی",
    "august": "اگست",
    "september": "ستمبر",
    "october": "اکتوبر",
    "november": "نومبر",
    "december": "دسمبر",
}

# =========================================================
# STOPWORDS
# =========================================================
COMMON_STOPWORDS = {
    "tum", "hum", "woh", "yeh", "dil", "ishq", "raat", "mein", "hai", 
    "aap", "main", "tere", "mera", "tera", "koi", "kya", "na", "se",
    "aur", "bhi", "to", "tha", "thi", "the", "ki", "ke", "ko",
    "se", "par", "pe", "tak", "liye", "baad", "pehle"
}

def is_generic_query(keyword):
    """Return True if query is too broad (stopword-only or very short)."""
    if not keyword:
        return True
    tokens = keyword.split()
    if len(tokens) <= 2 and all(t in COMMON_STOPWORDS for t in tokens):
        return True
    if len(keyword) < 3 and keyword.lower() in COMMON_STOPWORDS:
        return True
    return False

def suggest_alternative(keyword):
    """Return a helpful suggestion for generic queries."""
    suggestions = {
        "tum": "tum aaye, tum se, tumhare",
        "hum": "hum dono, hum na the, hum bhi",
        "woh": "woh log, woh din, woh baat",
        "dil": "dil hi to hai, dil dhadakta hai",
        "ishq": "ishq ne, ishq mein, ishq hai",
        "raat": "raat gayi, raat dhal gayi",
    }
    return suggestions.get(keyword.lower(), "Try adding more words (e.g., 'tum aaye', 'woh log')")

# =========================================================
# NORMALIZATION
# =========================================================
def normalize_roman(text):
    text = text.lower().strip()
    text = text.replace("aa", "a").replace("ee", "i").replace("oo", "u")
    return text

def normalize_urdu(text):
    if not text:
        return ""
    text = text.strip()
    replacements = {
        "ي": "ی",
        "ك": "ک",
        "ة": "ہ",
        "أ": "ا",
        "إ": "ا",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    text = re.sub(r"[^\u0600-\u06FF\s]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()

def roman_to_urdu(text):
    words = text.split()
    result = []
    for w in words:
        norm = normalize_roman(w)
        if any('\u0600' <= c <= '\u06FF' for c in w):
            result.append(w)
        else:
            result.append(ROMAN_DICT.get(norm, w))
    return " ".join(result)

def extract_matla_line(text):
    if not text:
        return ""
    lines = text.splitlines()
    cleaned = []
    for line in lines:
        line = normalize_urdu(line)
        if len(line) >= 3:
            cleaned.append(line)
    if cleaned:
        return cleaned[0]
    return normalize_urdu(text)

# =========================================================
# HIGHLIGHTING
# =========================================================
def highlight_matches(text, keyword):
    if not text or not keyword:
        return text
    pattern = re.compile(re.escape(keyword), re.IGNORECASE)
    return pattern.sub(lambda m: f"<mark>{m.group(0)}</mark>", text)

# =========================================================
# COSINE SIMILARITY
# =========================================================
def cosine_similarity(v1, v2):
    v1 = np.array(v1)
    v2 = np.array(v2)
    if v1.size == 0 or v2.size == 0:
        return 0.0
    norm1 = np.linalg.norm(v1)
    norm2 = np.linalg.norm(v2)
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return float(np.dot(v1, v2) / (norm1 * norm2 + 1e-8))

# =========================================================
# SEMANTIC SEARCH
# =========================================================
def semantic_search(query_embedding, top_n=50):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT ge.text_id, ge.embedding_vector, t.full_text_hash
        FROM ghazal_embeddings ge
        JOIN texts t ON ge.text_id = t.id
        WHERE t.is_deleted = FALSE
          AND t.full_text_hash IS NOT NULL
          AND ge.embedding_vector IS NOT NULL
    """)
    rows = cur.fetchall()
    cur.close()
    conn.close()

    scored = []
    for r in rows:
        emb = r['embedding_vector']
        if isinstance(emb, str):
            try:
                emb = json.loads(emb)
            except:
                continue
        if not emb:
            continue
        sim = cosine_similarity(query_embedding, emb)
        scored.append((r['text_id'], sim, r['full_text_hash']))

    scored.sort(key=lambda x: x[1], reverse=True)

    seen_hashes = set()
    filtered = []
    for tid, sim, fhash in scored:
        if fhash in seen_hashes:
            continue
        seen_hashes.add(fhash)
        filtered.append((tid, sim))

    return filtered[:top_n]

# =========================================================
# SIMPLE SEARCH FUNCTION (WORKING)
# =========================================================
def search_ghazals(filters):
    conn = get_db_connection()
    cur = conn.cursor()

    keyword = (filters.get('keyword') or '').strip()
    poet_id = filters.get('poet_id')
    contributor_id = filters.get('contributor_id')
    offset = filters.get('offset', 0)
    limit = filters.get('limit', 20)

    # Generic query protection
    if is_generic_query(keyword):
        return [], -1

    # Prepare search terms
    like_kw = f"%{keyword}%"
    urdu_kw = roman_to_urdu(keyword)
    like_ur = f"%{urdu_kw}%" if urdu_kw != keyword else like_kw

    # Build WHERE clause
    where_parts = ["COALESCE(t.is_deleted, FALSE) = FALSE"]
    params = []

    # Search conditions
    where_parts.append("""
        (t.normalized_matla ILIKE %s
         OR t.title_urdu ILIKE %s
         OR t.text_urdu ILIKE %s
         OR t.text_english ILIKE %s
         OR p.name ILIKE %s
         OR EXISTS (
             SELECT 1 FROM verses v
             WHERE v.text_id = t.id
             AND (v.misra1_urdu ILIKE %s OR v.misra2_urdu ILIKE %s)
         ))
    """)
    params.extend([like_ur, like_kw, like_kw, like_kw, like_kw, like_kw, like_kw])

    if poet_id:
        where_parts.append("t.poet_id = %s")
        params.append(poet_id)

    if contributor_id:
        where_parts.append("t.contributor_id = %s")
        params.append(contributor_id)

    where_clause = " AND ".join(where_parts)

    # Count total
    count_sql = f"""
        SELECT COUNT(DISTINCT t.id) AS total
        FROM texts t
        LEFT JOIN poets p ON p.id = t.poet_id
        WHERE {where_clause}
    """
    cur.execute(count_sql, params)
    total = cur.fetchone()['total']

    # Main query - fetch ALL columns needed for display
    query = f"""
        SELECT
            t.id,
            t.title_urdu,
            t.text_urdu,
            t.text_english,
            t.normalized_matla,
            t.form,
            COALESCE(p.name, 'Unknown') AS poet_name,
            COALESCE(p.name_urdu, '') AS poet_name_urdu,
            1 AS relevance,
            'General Match' AS match_type
        FROM texts t
        LEFT JOIN poets p ON p.id = t.poet_id
        WHERE {where_clause}
        ORDER BY t.id DESC
        LIMIT %s OFFSET %s
    """

    final_params = params + [limit, offset]
    cur.execute(query, final_params)
    results = cur.fetchall()

    # Apply highlighting AFTER fetching results
    for row in results:
        if row['text_urdu']:
            # Create highlighted version
            row['text_urdu_highlighted'] = highlight_matches(row['text_urdu'], keyword)
        else:
            row['text_urdu_highlighted'] = ''

    cur.close()
    conn.close()
    return results, total

# =========================================================
# SEARCH SUGGESTIONS
# =========================================================
def get_suggestions(query, limit=10):
    conn = get_db_connection()
    cur = conn.cursor()
    like_q = f"%{query}%"
    cur.execute("""
        SELECT DISTINCT suggestion FROM (
            SELECT normalized_matla AS suggestion FROM texts
            WHERE normalized_matla ILIKE %s AND COALESCE(is_deleted, FALSE) = FALSE
            UNION
            SELECT title_urdu FROM texts
            WHERE title_urdu ILIKE %s AND COALESCE(is_deleted, FALSE) = FALSE
            UNION
            SELECT name FROM poets
            WHERE name ILIKE %s
        ) s LIMIT %s
    """, (like_q, like_q, like_q, limit))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [r['suggestion'] for r in rows]

# =========================================================
# SMART SEARCH
# =========================================================
def smart_search(query, top_n=20):
    query_emb = generate_embedding(query)
    if not query_emb or len(query_emb) != 384:
        return []
    semantic = semantic_search(query_emb, top_n=50)
    if not semantic:
        return []
    ids = [tid for tid, _ in semantic]
    scores = {tid: score for tid, score in semantic}
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT DISTINCT ON (t.id)
            t.id, t.title_urdu, p.name AS poet_name,
            v.misra1_urdu, v.misra2_urdu
        FROM texts t
        JOIN poets p ON t.poet_id = p.id
        LEFT JOIN verses v ON v.text_id = t.id
        WHERE t.id = ANY(%s) AND t.is_deleted = FALSE
        ORDER BY t.id, v.couplet_index ASC NULLS LAST
    """, (ids,))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    results = []
    for r in rows:
        misra1 = r['misra1_urdu'] or ''
        misra2 = r['misra2_urdu'] or ''
        first_couplet = f"{misra1}\n{misra2}" if misra1 and misra2 else misra1
        results.append({
            "text_id": r['id'],
            "title": r['title_urdu'],
            "poet": r['poet_name'],
            "first_couplet": first_couplet,
            "score": round(scores.get(r['id'], 0), 3)
        })
    results.sort(key=lambda x: x['score'], reverse=True)
    return results[:top_n]
