# models/search_model.py
import json
import numpy as np
from models.base import get_db_connection
from modules.embeddings import generate_embedding   # for semantic search

# Safely import roman engine; if missing, define dummy function
try:
    from modules.roman_engine.matcher import process_query
except ImportError:
    def process_query(x):
        return x

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
        if any('\u0600' <= c <= '\u06FF' for c in w):
            urdu_words.append(w)
        else:
            urdu_words.append(ROMAN_DICT.get(norm, w))
    return " ".join(urdu_words)

def search_ghazals(filters):
    keyword = filters.get('keyword', '').strip()
    urdu_query = process_query(keyword) if keyword else ''
    poet_id = filters.get('poet_id')
    contributor_id = filters.get('contributor_id')
    offset = filters.get('offset', 0)
    limit = filters.get('limit', 20)

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            where_parts = []
            params = []

            if keyword:
                like_kw = f"%{keyword}%"
                conditions = []
                conditions.append("""
                    (t.title_urdu ILIKE %s OR t.title_english ILIKE %s OR
                     EXISTS (SELECT 1 FROM verses v WHERE v.text_id = t.id AND
                             (v.misra1_urdu ILIKE %s OR v.misra2_urdu ILIKE %s)))
                """)
                params.extend([like_kw, like_kw, like_kw, like_kw])
                if urdu_query and urdu_query != keyword:
                    like_ur = f"%{urdu_query}%"
                    conditions.append("""
                        (t.title_urdu ILIKE %s OR
                         EXISTS (SELECT 1 FROM verses v WHERE v.text_id = t.id AND
                                 (v.misra1_urdu ILIKE %s OR v.misra2_urdu ILIKE %s)))
                    """)
                    params.extend([like_ur, like_ur, like_ur])
                where_parts.append("(" + " OR ".join(conditions) + ")")

            if poet_id:
                where_parts.append("t.poet_id = %s")
                params.append(poet_id)

            if contributor_id:
                where_parts.append("t.contributor_id = %s")
                params.append(contributor_id)

            where_clause = " AND ".join(where_parts) if where_parts else "1=1"

            # Count total
            count_query = f"""
                SELECT COUNT(DISTINCT t.id) as total
                FROM texts t
                WHERE t.form = 'ghazal' AND {where_clause}
            """
            cur.execute(count_query, params)
            total = cur.fetchone()['total']

            # Fetch first verse for display
            query = f"""
                SELECT DISTINCT
                    t.id as text_id,
                    t.title_urdu,
                    t.title_english,
                    p.name as poet_name,
                    p.name_urdu as poet_name_urdu,
                    v.misra1_urdu,
                    v.misra2_urdu,
                    v.misra1_english,
                    v.misra2_english
                FROM texts t
                JOIN poets p ON p.id = t.poet_id
                LEFT JOIN verses v ON v.text_id = t.id AND v.couplet_index = 1
                WHERE t.form = 'ghazal' AND {where_clause}
                ORDER BY t.id DESC
                LIMIT %s OFFSET %s
            """
            final_params = params + [limit, offset]
            cur.execute(query, final_params)
            rows = cur.fetchall()

            # Group results (already distinct by text_id)
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
    urdu_q = process_query(q)
    like_pattern = f"%{urdu_q}%"
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            try:
                cur.execute("""
                    SELECT DISTINCT suggestion FROM (
                        SELECT title_urdu AS suggestion
                        FROM texts
                        WHERE title_urdu ILIKE %s
                        UNION
                        SELECT misra1_urdu
                        FROM verses
                        WHERE misra1_urdu ILIKE %s
                        UNION
                        SELECT misra1_urdu
                        FROM verses
                        WHERE similarity(misra1_urdu, %s) > 0.2
                    ) s
                    LIMIT 10
                """, (like_pattern, like_pattern, urdu_q))
            except Exception:
                # Fallback if pg_trgm not available
                cur.execute("""
                    SELECT title_urdu AS suggestion FROM texts WHERE title_urdu ILIKE %s
                    UNION
                    SELECT misra1_urdu FROM verses WHERE misra1_urdu ILIKE %s
                    LIMIT 10
                """, (like_pattern, like_pattern))
            rows = cur.fetchall()
            return [r['suggestion'] for r in rows]

# ================= HYBRID SEMANTIC SEARCH =================
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

def semantic_search(query_embedding, top_n=50):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT text_id, embedding_vector FROM ghazal_embeddings")
    rows = cur.fetchall()
    cur.close()
    conn.close()

    results = []
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
        results.append((r['text_id'], sim))

    results.sort(key=lambda x: x[1], reverse=True)
    return results[:top_n]

def smart_search(query, top_n=20):
    """
    Convert query to embedding, find top N semantically similar ghazals,
    return list with titles, poets, and similarity scores.
    """
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
        SELECT t.id, t.title_urdu, p.name as poet_name
        FROM texts t
        JOIN poets p ON t.poet_id = p.id
        WHERE t.id = ANY(%s)
    """, (ids,))
    rows = cur.fetchall()
    cur.close()
    conn.close()

    results = []
    for r in rows:
        results.append({
            "text_id": r['id'],
            "title": r['title_urdu'],
            "poet": r['poet_name'],
            "score": round(scores.get(r['id'], 0), 3)
        })
    results.sort(key=lambda x: x['score'], reverse=True)
    return results[:top_n]