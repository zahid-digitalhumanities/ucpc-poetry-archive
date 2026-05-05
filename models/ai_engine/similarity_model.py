# models/similarity_model.py
import json
import numpy as np
from models.base import get_db_connection

W_EMB = 0.7
W_RADIF = 0.1
W_QAAFIYA = 0.1
W_THEME = 0.1

def cosine_similarity(vec1, vec2):
    try:
        v1 = np.array(vec1, dtype=float)
        v2 = np.array(vec2, dtype=float)
        if v1.size == 0 or v2.size == 0:
            return 0.0
        norm1, norm2 = np.linalg.norm(v1), np.linalg.norm(v2)
        if norm1 == 0 or norm2 == 0:
            return 0.0
        return float(np.dot(v1, v2) / (norm1 * norm2 + 1e-8))
    except:
        return 0.0

def parse_embedding(emb):
    if emb is None:
        return None
    if isinstance(emb, str):
        try:
            emb = json.loads(emb)
        except:
            return None
    if not isinstance(emb, list) or len(emb) == 0:
        return None
    return emb

def safe_equal(a, b):
    return 1.0 if a and b and str(a).strip() == str(b).strip() else 0.0

def overlap_ratio(list1, list2):
    if not list1 or not list2:
        return 0.0
    set1, set2 = set(list1), set(list2)
    return len(set1 & set2) / max(len(set1), 1)

def find_similar_ghazals(text_id, top_n=10, prefilter_n=50):
    conn = get_db_connection()
    cur = conn.cursor()

    # --- get target embedding ---
    cur.execute("SELECT embedding_vector FROM ghazal_embeddings WHERE text_id = %s", (text_id,))
    t_row = cur.fetchone()
    if not t_row:
        cur.close(); conn.close(); return []
    t_emb = parse_embedding(t_row['embedding_vector'])
    if not t_emb:
        cur.close(); conn.close(); return []

    # --- get target poetic features ---
    cur.execute("SELECT radif, qaafiya, theme FROM poetic_features WHERE text_id = %s", (text_id,))
    t_feat = cur.fetchone()
    t_radif = t_feat['radif'] if t_feat else None
    t_qaafiya = t_feat['qaafiya'] if t_feat else []
    t_theme = t_feat['theme'] if t_feat else None

    # --- get all candidate embeddings ---
    cur.execute("SELECT text_id, embedding_vector FROM ghazal_embeddings WHERE text_id != %s AND embedding_vector IS NOT NULL", (text_id,))
    rows = cur.fetchall()
    cur.close()
    conn.close()

    candidates = []
    for r in rows:
        c_emb = parse_embedding(r['embedding_vector'])
        if not c_emb:
            continue
        emb_sim = cosine_similarity(t_emb, c_emb)
        if emb_sim > 0:
            candidates.append((r['text_id'], emb_sim))

    candidates.sort(key=lambda x: x[1], reverse=True)
    top_candidates = candidates[:prefilter_n]

    # --- fetch features for candidates in one batch ---
    if not top_candidates:
        return []
    ids = [c[0] for c in top_candidates]
    conn2 = get_db_connection()
    cur2 = conn2.cursor()
    cur2.execute("""
        SELECT text_id, radif, qaafiya, theme
        FROM poetic_features
        WHERE text_id = ANY(%s)
    """, (ids,))
    feat_rows = cur2.fetchall()
    cur2.close()
    conn2.close()

    feat_map = {row['text_id']: row for row in feat_rows}

    results = []
    for cand_id, emb_score in top_candidates:
        feat = feat_map.get(cand_id, {})
        c_radif = feat.get('radif')
        c_qaafiya = feat.get('qaafiya') or []
        c_theme = feat.get('theme')

        radif_score = safe_equal(t_radif, c_radif)
        qaafiya_score = overlap_ratio(t_qaafiya, c_qaafiya)
        theme_score = safe_equal(t_theme, c_theme)

        final_score = (W_EMB * emb_score +
                       W_RADIF * radif_score +
                       W_QAAFIYA * qaafiya_score +
                       W_THEME * theme_score)

        breakdown = {
            'embedding': round(emb_score, 3),
            'radif': radif_score,
            'qaafiya': round(qaafiya_score, 3),
            'theme': theme_score
        }
        explanation_text = [
            f"Semantic similarity: {emb_score:.2f}",
            f"Radif match: {'Yes' if radif_score else 'No'}",
            f"Qaafiya overlap: {qaafiya_score:.0%}",
            f"Theme match: {'Yes' if theme_score else 'No'}"
        ]
        results.append({
            'text_id': cand_id,
            'similarity': round(final_score, 3),
            'explanation': {
                'embedding_score': round(emb_score, 3),
                'breakdown': breakdown,
                'explanation_text': explanation_text
            }
        })

    results.sort(key=lambda x: x['similarity'], reverse=True)
    return results[:top_n]