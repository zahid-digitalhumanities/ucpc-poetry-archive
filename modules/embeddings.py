# modules/embeddings.py
from sentence_transformers import SentenceTransformer
from models.base import get_db_connection
import numpy as np
import json

# Load the multilingual model once (cached)
_model = None

def get_model():
    global _model
    if _model is None:
        _model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
    return _model

def get_ghazal_text(conn, text_id):
    """
    Retrieve the full text of a ghazal (all misras concatenated).
    Used for generating the embedding.
    """
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
        if r['misra1_urdu']:
            lines.append(r['misra1_urdu'])
        if r['misra2_urdu']:
            lines.append(r['misra2_urdu'])
    return ' '.join(lines)

def update_ghazal_embedding(text_id):
    """
    Compute and store the embedding for a single ghazal.
    Stores both JSONB and float array (for pgvector compatibility) and the norm.
    """
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        text = get_ghazal_text(conn, text_id)
        if not text:
            print(f"Warning: Ghazal {text_id} has no text; skipping embedding.")
            return

        model = get_model()
        embedding = model.encode(text)  # numpy array
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
    v1 = np.array(e1['embedding_vector'])
    v2 = np.array(e2['embedding_vector'])
    similarity = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))
    return float(similarity)