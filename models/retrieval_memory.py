# models/retrieval_memory.py
"""
Check if a ghazal already exists in corpus before ML prediction.
"""

from models.base import get_db_connection
from modules.text_normalizer import normalize_urdu
from modules.embeddings import generate_embedding, cosine_similarity
import numpy as np

def corpus_lookup(text: str, similarity_threshold: float = 0.92) -> dict:
    """
    First check exact matches, then near duplicates via embedding similarity.
    If found, return the poet instead of running ML.
    """
    normalized = normalize_urdu(text)
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    # 1. Exact normalized match
    cur.execute("""
        SELECT t.id, t.poet_id, p.name, t.text_urdu
        FROM texts t
        JOIN poets p ON t.poet_id = p.id
        WHERE t.form = 'ghazal'
          AND t.is_deleted = FALSE
          AND t.integrity_status = 'clean'
          AND t.normalized_text = %s
        LIMIT 1
    """, (normalized,))
    row = cur.fetchone()
    if row:
        cur.close()
        conn.close()
        return {
            'found': True,
            'match_type': 'exact',
            'poet_id': row[1],
            'poet_name': row[2],
            'text_id': row[0],
            'confidence': 100.0
        }
    
    # 2. Near duplicate using existing embeddings (if available)
    # Generate embedding for the input
    try:
        input_emb = generate_embedding(text)
        cur.execute("""
            SELECT t.id, t.poet_id, p.name, g.embedding_vector
            FROM texts t
            JOIN poets p ON t.poet_id = p.id
            JOIN ghazal_embeddings g ON t.id = g.text_id
            WHERE t.form = 'ghazal' AND t.is_deleted = FALSE
            ORDER BY t.id
            LIMIT 100
        """)
        rows = cur.fetchall()
        best_sim = 0.0
        best_row = None
        for r in rows:
            emb = r[3]
            if emb is None:
                continue
            # Convert string to list if needed
            if isinstance(emb, str):
                import json
                emb = json.loads(emb)
            sim = cosine_similarity(np.array(input_emb), np.array(emb))
            if sim > best_sim:
                best_sim = sim
                best_row = r
        if best_sim >= similarity_threshold:
            cur.close()
            conn.close()
            return {
                'found': True,
                'match_type': 'near_duplicate',
                'poet_id': best_row[1],
                'poet_name': best_row[2],
                'text_id': best_row[0],
                'similarity': best_sim,
                'confidence': best_sim * 100
            }
    except Exception as e:
        print(f"Near-duplicate search failed: {e}")
    
    cur.close()
    conn.close()
    return {'found': False}