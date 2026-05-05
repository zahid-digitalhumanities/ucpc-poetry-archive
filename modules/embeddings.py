from sentence_transformers import SentenceTransformer
from models.base import get_db_connection
import numpy as np
import json
import re

# ================= MODEL CACHE =================
_model = None

def get_model():
    global _model
    if _model is None:
        print("🔄 Loading embedding model...")
        _model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
        print("✅ Embedding model loaded")
    return _model


# ================= NORMALIZATION =================
def normalize_urdu(text):
    if not text:
        return ""

    text = text.strip()
    text = re.sub(r'\s+', ' ', text)

    # remove punctuation
    text = re.sub(r'[،۔.!?]', '', text)

    return text


# ================= FETCH TEXT (IMPROVED) =================
def get_ghazal_lines(conn, text_id):
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
            lines.append(normalize_urdu(r['misra1_urdu']))
        if r['misra2_urdu']:
            lines.append(normalize_urdu(r['misra2_urdu']))

    return lines


# ================= SMART EMBEDDING =================
def build_ghazal_embedding(lines):
    """
    🔥 KEY UPGRADE:
    - Encode line by line
    - Weighted average
    """

    if not lines:
        return np.zeros(384)

    model = get_model()

    embeddings = model.encode(lines)

    # Weighting: first couplet more important
    weights = []

    for i in range(len(lines)):
        if i < 2:
            weights.append(2.0)  # matla weight
        else:
            weights.append(1.0)

    weights = np.array(weights).reshape(-1, 1)

    weighted = embeddings * weights
    final_vec = np.sum(weighted, axis=0) / np.sum(weights)

    return final_vec


# ================= STORE EMBEDDING =================
def update_ghazal_embedding(text_id):
    conn = get_db_connection()
    cur = conn.cursor()

    try:
        lines = get_ghazal_lines(conn, text_id)

        if not lines:
            print(f"⚠️ No text for {text_id}")
            return

        embedding = build_ghazal_embedding(lines)
        emb_list = embedding.tolist()
        norm = float(np.linalg.norm(embedding))

        cur.execute("""
            INSERT INTO ghazal_embeddings
            (text_id, embedding, embedding_vector, embedding_norm, updated_at)
            VALUES (%s, %s, %s, %s, NOW())
            ON CONFLICT (text_id)
            DO UPDATE SET
                embedding = EXCLUDED.embedding,
                embedding_vector = EXCLUDED.embedding_vector,
                embedding_norm = EXCLUDED.embedding_norm,
                updated_at = NOW()
        """, (
            text_id,
            json.dumps(emb_list),
            emb_list,
            norm
        ))

        conn.commit()
        print(f"✅ Embedded ghazal {text_id}")

    except Exception as e:
        print(f"❌ Embedding error {text_id}: {e}")
        conn.rollback()

    finally:
        cur.close()
        conn.close()


# ================= FAST EMBEDDING =================
def generate_embedding(text):
    try:
        text = normalize_urdu(text)

        if not text:
            return [0.0] * 384

        model = get_model()
        emb = model.encode([text])[0]

        return emb.tolist()

    except Exception as e:
        print(f"❌ embedding error: {e}")
        return [0.0] * 384


# ================= COSINE (OPTIMIZED) =================
def cosine_similarity(v1, v2):
    try:
        v1 = np.array(v1)
        v2 = np.array(v2)

        if v1.size == 0 or v2.size == 0:
            return 0.0

        return float(np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2) + 1e-8))

    except:
        return 0.0


# ================= 🔥 FAST DB SIMILARITY =================
def fast_similarity_search(query_vec, top_n=20):

    conn = get_db_connection()
    cur = conn.cursor()

    try:
        cur.execute("""
            SELECT text_id, embedding_vector, embedding_norm
            FROM ghazal_embeddings
        """)

        rows = cur.fetchall()

        q = np.array(query_vec)
        q_norm = np.linalg.norm(q)

        results = []

        for r in rows:
            emb = r['embedding_vector']
            norm = r['embedding_norm'] or 1e-8

            v = np.array(emb)

            score = float(np.dot(q, v) / (q_norm * norm + 1e-8))

            results.append((r['text_id'], score))

        results.sort(key=lambda x: x[1], reverse=True)

        return results[:top_n]

    finally:
        cur.close()
        conn.close()


# ================= 🔥 POET PREDICTION (IMPROVED) =================
def predict_poet_by_similarity(input_text, top_n=3):

    conn = get_db_connection()
    cur = conn.cursor()

    try:
        query_vec = generate_embedding(input_text)

        cur.execute("""
            SELECT g.embedding_vector, g.embedding_norm, t.poet_id
            FROM ghazal_embeddings g
            JOIN texts t ON g.text_id = t.id
        """)

        rows = cur.fetchall()

        scores = {}
        counts = {}

        q = np.array(query_vec)
        q_norm = np.linalg.norm(q)

        for r in rows:
            poet_id = r['poet_id']
            v = np.array(r['embedding_vector'])
            norm = r['embedding_norm'] or 1e-8

            sim = float(np.dot(q, v) / (q_norm * norm + 1e-8))

            scores[poet_id] = scores.get(poet_id, 0) + sim
            counts[poet_id] = counts.get(poet_id, 0) + 1

        poet_scores = []

        for pid in scores:
            avg = scores[pid] / counts[pid]
            poet_scores.append((pid, avg))

        poet_scores.sort(key=lambda x: x[1], reverse=True)

        results = []

        for pid, score in poet_scores[:top_n]:
            cur.execute("SELECT name FROM poets WHERE id=%s", (pid,))
            row = cur.fetchone()

            results.append({
                "poet_id": pid,
                "poet_name": row['name'] if row else "Unknown",
                "confidence": round(score, 3)
            })

        return results

    except Exception as e:
        print(f"❌ prediction error: {e}")
        return []

    finally:
        cur.close()
        conn.close()