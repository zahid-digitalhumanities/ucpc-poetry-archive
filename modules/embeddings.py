# modules/embeddings.py - Free tier placeholder
# Heavy ML models (sentence_transformers, torch) are disabled to save memory.
# This placeholder prevents import errors while keeping the app functional.

import os
import json
import numpy as np

# Check if embeddings are disabled (default: true on free tier)
EMBEDDINGS_DISABLED = os.getenv('DISABLE_SEMANTIC', 'true') == 'true'

def get_model():
    """Placeholder - returns None since embeddings are disabled."""
    if EMBEDDINGS_DISABLED:
        return None
    try:
        # This will only run if embeddings are re-enabled
        from sentence_transformers import SentenceTransformer
        return SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
    except ImportError:
        print("⚠️ sentence_transformers not installed. Embeddings disabled.")
        return None

def get_ghazal_text(conn, text_id):
    """Retrieve the full text of a ghazal (all misras concatenated)."""
    cur = conn.cursor()
    cur.execute("""
        SELECT misra1_urdu, misra2_urdu
        FROM verses
        WHERE text_id = %s
        ORDER BY couplet_index
    """, (text_id,))
    rows = cur.fetchall()
    cur.close()

    lines = []
    for r in rows:
        if isinstance(r, dict):
            if r.get('misra1_urdu'):
                lines.append(r['misra1_urdu'])
            if r.get('misra2_urdu'):
                lines.append(r['misra2_urdu'])
        else:
            if r[0]:
                lines.append(r[0])
            if r[1]:
                lines.append(r[1])
    return ' '.join(lines)

def update_ghazal_embedding(text_id):
    """
    Placeholder - embeddings disabled on free tier.
    Returns None without doing any heavy computation.
    """
    if EMBEDDINGS_DISABLED:
        print(f"⚠️ Embeddings disabled - skipping update for ghazal {text_id}")
        return None
    
    # Full implementation (only runs if re-enabled)
    from models.base import get_db_connection
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        text = get_ghazal_text(conn, text_id)
        if not text:
            print(f"Warning: Ghazal {text_id} has no text; skipping embedding.")
            return

        model = get_model()
        if model is None:
            print(f"⚠️ No model available - skipping ghazal {text_id}")
            return
            
        embedding = model.encode(text)
        embedding_list = embedding.tolist()
        norm = float(np.linalg.norm(embedding))

        cur.execute("""
            INSERT INTO ghazal_embeddings (text_id, embedding, embedding_vector, embedding_norm, updated_at)
            VALUES (%s, %s, %s, %s, NOW())
            ON CONFLICT (text_id) DO UPDATE
            SET embedding = EXCLUDED.embedding,
                embedding_vector = EXCLUDED.embedding_vector,
                embedding_norm = EXCLUDED.embedding_norm,
                updated_at = NOW()
        """, (text_id, json.dumps(embedding_list), embedding_list, norm))
        conn.commit()
        print(f"✅ Embedded ghazal {text_id}")
    except Exception as e:
        print(f"❌ Error embedding ghazal {text_id}: {e}")
        conn.rollback()
    finally:
        cur.close()
        conn.close()

def cosine_similarity(vec1, vec2):
    """Compute cosine similarity between two vectors (lists or arrays)."""
    v1 = np.array(vec1)
    v2 = np.array(vec2)
    if v1.size == 0 or v2.size == 0:
        return 0.0
    return float(np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2) + 1e-8))

def get_similarity_score(text_id_1, text_id_2):
    """Returns cosine similarity between two ghazal embeddings (0–1)."""
    if EMBEDDINGS_DISABLED:
        return 0.0
    
    from models.base import get_db_connection
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT embedding_vector FROM ghazal_embeddings WHERE text_id = %s", (text_id_1,))
    e1 = cur.fetchone()
    cur.execute("SELECT embedding_vector FROM ghazal_embeddings WHERE text_id = %s", (text_id_2,))
    e2 = cur.fetchone()
    cur.close()
    conn.close()
    
    if not e1 or not e2:
        return 0.0
    
    v1 = np.array(e1['embedding_vector'] if isinstance(e1, dict) else e1[0])
    v2 = np.array(e2['embedding_vector'] if isinstance(e2, dict) else e2[0])
    similarity = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2) + 1e-8)
    return float(similarity)

def batch_update_embeddings():
    """Placeholder - does nothing on free tier."""
    if EMBEDDINGS_DISABLED:
        print("⚠️ Batch embeddings disabled on free tier")
        return 0
    
    print("Batch embeddings would run here if enabled")
    return 0
