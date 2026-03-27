# models/search_model.py
import psycopg2
import psycopg2.extras
from models.ghazal_model import get_db

# ---------- Roman → Urdu dictionary ----------
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
    "zaman": "زمان",
    "safar": "سفر",
    "manzil": "منزل",
    "dunya": "دنیا",
    "khushi": "خوشی",
    "gham": "غم",
    "aansu": "آنسو",
    "rooh": "روح",
    "jaan": "جان",
    "yeh": "یہ",
    "woh": "وہ",
    "hai": "ہے",
    "hain": "ہیں",
    "tha": "تھا",
    "thi": "تھی",
    "the": "تھے",
    "main": "میں",
    "tu": "تو",
    "ap": "آپ",
    "us": "اس",
    "is": "اس",
    "ko": "کو",
    "se": "سے",
    "ka": "کا",
    "ki": "کی",
    "ke": "کے",
    "par": "پر",
    "mein": "میں",
    "ne": "نے",
    "ghalib": "غالب",
    "iqbal": "اقبال",
    "faiz": "فیض",
    "mir": "میر",
    "faraz": "فراز",
    "parveen": "پروین",
    "shakir": "شاکر",
    "nasir": "ناصر",
    "kazmi": "کاظمی",
    "sahir": "ساحر",
    "ludhianvi": "لدھیانوی",
    # English words
    "night": "رات",
    "love": "محبت",
    "lonely": "تنہائی",
    "alone": "تنہا",
    "sad": "غم",
    "happy": "خوش",
    "heart": "دل",
    "life": "زندگی",
    "death": "موت",
    "sky": "آسمان",
    "moon": "چاند",
    "star": "ستارہ",
    "flower": "پھول",
    "garden": "گلشن",
    "friend": "دوست",
    "enemy": "دشمن",
    "pain": "درد",
    "sorrow": "غم",
    "hope": "امید",
    "waiting": "انتظار",
}

def normalize_roman(text):
    text = text.lower().strip()
    text = text.replace("aa", "a").replace("ee", "i").replace("oo", "u")
    return text

def roman_to_urdu(text):
    words = text.split()
    urdu_words = []
    for w in words:
        norm = normalize_roman(w)
        # If already contains Urdu characters, keep as is
        if any('\u0600' <= c <= '\u06FF' for c in w):
            urdu_words.append(w)
        else:
            urdu_words.append(ROMAN_DICT.get(norm, w))
    return " ".join(urdu_words)

# ---------- Search functions ----------
def search_ghazals(filters):
    keyword = filters.get('keyword', '').strip()
    urdu_query = roman_to_urdu(keyword) if keyword else ''
    poet_id = filters.get('poet_id')
    contributor_id = filters.get('contributor_id')
    offset = filters.get('offset', 0)
    limit = filters.get('limit', 20)

    conn = get_db()
    cur = conn.cursor()

    where_parts = []
    params = []

    # Keyword search – hybrid: ILIKE + fuzzy similarity
    if keyword:
        like_kw = f"%{keyword}%"
        conditions = []

        # 1. Exact/ILIKE search
        conditions.append("""
            (t.title_urdu ILIKE %s OR t.title_english ILIKE %s OR
             EXISTS (
                 SELECT 1 FROM verses v
                 WHERE v.text_id = t.id AND
                 (v.misra1_urdu ILIKE %s OR v.misra2_urdu ILIKE %s)
             ))
        """)
        params.extend([like_kw, like_kw, like_kw, like_kw])

        # 2. Fuzzy similarity search (if converted Urdu exists)
        if urdu_query:
            conditions.append("""
                (similarity(t.title_urdu, %s) > 0.2 OR
                 EXISTS (
                     SELECT 1 FROM verses v
                     WHERE v.text_id = t.id AND
                     (similarity(v.misra1_urdu, %s) > 0.2 OR
                      similarity(v.misra2_urdu, %s) > 0.2)
                 ))
            """)
            params.extend([urdu_query, urdu_query, urdu_query])

        where_parts.append("(" + " OR ".join(conditions) + ")")

    if poet_id:
        where_parts.append("t.poet_id = %s")
        params.append(poet_id)

    if contributor_id:
        where_parts.append("t.contributor_id = %s")
        params.append(contributor_id)

    where_clause = " AND ".join(where_parts) if where_parts else "1=1"

    # Build SELECT list. Include similarity score if fuzzy search is used.
    select_fields = """
        t.id as text_id,
        t.title_urdu,
        t.title_english,
        p.name as poet_name,
        p.name_urdu as poet_name_urdu,
        v.misra1_urdu,
        v.misra2_urdu,
        v.misra1_english,
        v.misra2_english
    """
    if urdu_query:
        select_fields = f"{select_fields}, similarity(t.title_urdu, %s) as score"
        params.append(urdu_query)  # extra param for the score calculation

    # Build ORDER BY
    order_by = "t.id DESC"
    if urdu_query:
        # Use score in order by; we already added it to select list
        order_by = "score DESC NULLS LAST, t.id DESC"

    query = f"""
        SELECT {select_fields}
        FROM texts t
        JOIN poets p ON p.id = t.poet_id
        LEFT JOIN verses v ON v.text_id = t.id AND v.couplet_index = 1
        WHERE t.form = 'ghazal' AND {where_clause}
        ORDER BY {order_by}
        LIMIT %s OFFSET %s
    """
    # Note: the score param is already in params; we add limit/offset at the end
    final_params = params + [limit, offset]
    cur.execute(query, final_params)
    rows = cur.fetchall()

    # Count total (remove the score param from params list if it was added)
    count_params = params.copy()
    if urdu_query:
        # The last param added for score is not needed for count
        count_params = count_params[:-1]  # remove the extra score param
    count_query = f"""
        SELECT COUNT(DISTINCT t.id) as total
        FROM texts t
        WHERE t.form = 'ghazal' AND {where_clause}
    """
    cur.execute(count_query, count_params)
    total = cur.fetchone()['total']

    cur.close()
    conn.close()

    # Group results (avoid duplicates in case of multiple verses, though we took first)
    grouped = {}
    for row in rows:
        tid = row['text_id']
        if tid not in grouped:
            grouped[tid] = {
                'text_id': tid,
                'title_urdu': row['title_urdu'],
                'title_english': row['title_english'],
                'poet_name': row['poet_name'],
                'poet_name_urdu': row['poet_name_urdu'],
                'first_verse_urdu': f"{row['misra1_urdu']}\n{row['misra2_urdu']}" if row['misra2_urdu'] else row['misra1_urdu'],
                'first_verse_english': f"{row['misra1_english']}\n{row['misra2_english']}" if row['misra2_english'] else row['misra1_english'],
            }
    return list(grouped.values()), total

def get_suggestions(q):
    """Return ranked suggestions based on fuzzy similarity."""
    urdu_q = roman_to_urdu(q)
    if not urdu_q:
        return []

    conn = get_db()
    cur = conn.cursor()

    try:
        # Try using trigram similarity if available
        cur.execute("""
            SELECT suggestion FROM (
                SELECT title_urdu AS suggestion,
                       similarity(title_urdu, %s) AS score
                FROM texts
                WHERE similarity(title_urdu, %s) > 0.2

                UNION

                SELECT misra1_urdu,
                       similarity(misra1_urdu, %s)
                FROM verses
                WHERE similarity(misra1_urdu, %s) > 0.2
            ) s
            ORDER BY score DESC
            LIMIT 10
        """, (urdu_q, urdu_q, urdu_q, urdu_q))
        rows = cur.fetchall()
    except Exception:
        # Fallback to ILIKE if trigram not available
        like_pattern = f"%{urdu_q}%"
        cur.execute("""
            SELECT title_urdu AS suggestion FROM texts WHERE title_urdu ILIKE %s
            UNION
            SELECT misra1_urdu FROM verses WHERE misra1_urdu ILIKE %s
            LIMIT 10
        """, (like_pattern, like_pattern))
        rows = cur.fetchall()

    suggestions = [r['suggestion'] for r in rows]
    cur.close()
    conn.close()
    return suggestions

def get_stats():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM poets")
    poets = cur.fetchone()['count']
    cur.execute("SELECT COUNT(*) FROM texts WHERE form = 'ghazal'")
    texts = cur.fetchone()['count']
    cur.execute("SELECT COUNT(*) FROM verses")
    verses = cur.fetchone()['count']
    cur.close()
    conn.close()
    return {'total_poets': poets, 'total_ghazals': texts, 'texts': texts, 'total_verses': verses, 'verses': verses}

def get_all_poets():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT p.id, p.name, p.name_urdu, p.birth_year, p.death_year,
               COUNT(t.id) AS ghazal_count
        FROM poets p
        LEFT JOIN texts t ON t.poet_id = p.id AND t.form = 'ghazal'
        GROUP BY p.id
        ORDER BY p.name
    """)
    poets = cur.fetchall()
    cur.close()
    conn.close()
    return poets

def get_all_contributors():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT id, name FROM contributors ORDER BY name")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows