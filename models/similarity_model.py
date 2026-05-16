# models/similarity_model.py
import json
import numpy as np
from models.base import get_db_connection
from modules.explainability import explain_similarity

def cosine_similarity(vec1, vec2):
    v1 = np.array(vec1)
    v2 = np.array(vec2)
    if v1.size == 0 or v2.size == 0:
        return 0.0
    return float(np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2) + 1e-8))

def find_similar_ghazals(text_id, top_n=10, prefilter_n=50):
    conn = get_db_connection()
    cur = conn.cursor()

    # Get target embedding
    cur.execute("SELECT embedding_vector FROM ghazal_embeddings WHERE text_id = %s", (text_id,))
    target_row = cur.fetchone()
    if not target_row:
        cur.close()
        conn.close()
        return []
    target_emb = target_row['embedding_vector']
    if isinstance(target_emb, str):
        target_emb = json.loads(target_emb)

    # Get all other embeddings
    cur.execute("SELECT text_id, embedding_vector FROM ghazal_embeddings WHERE text_id != %s", (text_id,))
    rows = cur.fetchall()
    cur.close()
    conn.close()

    # Stage 1: Embedding prefilter
    candidates = []
    for r in rows:
        cand_emb = r['embedding_vector']
        if isinstance(cand_emb, str):
            cand_emb = json.loads(cand_emb)
        sim = cosine_similarity(target_emb, cand_emb)
        candidates.append((r['text_id'], sim))

    candidates.sort(key=lambda x: x[1], reverse=True)
    top_candidates = candidates[:prefilter_n]

    # Stage 2: Explainable reranking
    results = []
    for cand_id, emb_score in top_candidates:
        exp = explain_similarity(text_id, cand_id)   # returns dict with 'breakdown', 'explanation'

        final_score = (
            0.5 * emb_score +
            exp['breakdown'].get('radif', 0) +
            exp['breakdown'].get('qaafiya', 0) +
            exp['breakdown'].get('theme', 0)
        )

        results.append({
            'text_id': cand_id,
            'similarity': round(final_score, 3),
            'explanation': {
                'embedding_score': round(emb_score, 3),
                'breakdown': exp['breakdown'],
                'explanation_text': exp['explanation']
            }
        })

    results.sort(key=lambda x: x['similarity'], reverse=True)
    return results[:top_n]