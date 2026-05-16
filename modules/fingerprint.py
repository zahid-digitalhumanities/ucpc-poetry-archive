import numpy as np
import json
from collections import Counter
from models.base import get_db_connection

def build_poet_fingerprint(poet_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT g.embedding_vector
        FROM texts t
        JOIN ghazal_embeddings g ON t.id = g.text_id
        WHERE t.poet_id = %s
    """, (poet_id,))
    rows = cur.fetchall()
    if not rows:
        return
    embeddings = [r['embedding_vector'] for r in rows]
    avg_embedding = np.mean(embeddings, axis=0).tolist()

    # Radif distribution
    cur.execute("""
        SELECT pf.radif
        FROM poetic_features pf
        JOIN texts t ON pf.text_id = t.id
        WHERE t.poet_id = %s
    """, (poet_id,))
    radifs = [r['radif'] for r in cur.fetchall() if r['radif']]
    common_radif = Counter(radifs).most_common(5)

    # Meter – column may not exist; handle gracefully
    try:
        cur.execute("""
            SELECT pf.meter
            FROM poetic_features pf
            JOIN texts t ON pf.text_id = t.id
            WHERE t.poet_id = %s
        """, (poet_id,))
        meters = [r['meter'] for r in cur.fetchall() if r['meter']]
        meter_dist = dict(Counter(meters))
    except Exception:
        meter_dist = {}

    stylistic_features = {
        "common_radif": common_radif,
        "meter_distribution": meter_dist
    }
    # Convert to JSON string for JSONB column
    stylistic_json = json.dumps(stylistic_features, ensure_ascii=False)

    cur.execute("""
        INSERT INTO poet_fingerprints
        (poet_id, avg_embedding, stylistic_features, updated_at)
        VALUES (%s, %s, %s, NOW())
        ON CONFLICT (poet_id) DO UPDATE
        SET avg_embedding = EXCLUDED.avg_embedding,
            stylistic_features = EXCLUDED.stylistic_features,
            updated_at = NOW()
    """, (poet_id, avg_embedding, stylistic_json))
    conn.commit()
    cur.close()
    conn.close()

def predict_poet(text_id):
    conn = get_db_connection()
    cur = conn.cursor()

    # Get target embedding and poetic features
    cur.execute("""
        SELECT g.embedding_vector,
               pf.radif, pf.qaafiya
        FROM ghazal_embeddings g
        JOIN texts t ON g.text_id = t.id
        LEFT JOIN poetic_features pf ON t.id = pf.text_id
        WHERE g.text_id = %s
    """, (text_id,))
    target_row = cur.fetchone()
    if not target_row:
        cur.close()
        conn.close()
        return []
    target_vec = target_row['embedding_vector']
    if isinstance(target_vec, str):
        target_vec = json.loads(target_vec)
    target_radif = target_row['radif'] or ''
    target_qaafiya = set(target_row['qaafiya'] or [])

    # Get all poet fingerprints
    cur.execute("SELECT poet_id, avg_embedding, stylistic_features FROM poet_fingerprints")
    poets = cur.fetchall()
    cur.close()
    conn.close()

    from modules.embeddings import cosine_similarity
    results = []
    for p in poets:
        poet_id = p['poet_id']
        avg_emb = p['avg_embedding']
        if isinstance(avg_emb, str):
            avg_emb = json.loads(avg_emb)
        if not avg_emb:
            continue

        # 1. Embedding similarity
        emb_sim = cosine_similarity(target_vec, avg_emb)

        # 2. Radif pattern match – check if target radif is among poet's common radifs
        stylistic = p['stylistic_features']
        if isinstance(stylistic, str):
            stylistic = json.loads(stylistic)
        common_radifs = [r[0] for r in stylistic.get('common_radif', [])]
        radif_match = 1.0 if target_radif in common_radifs else 0.0

        # 3. Qaafiya pattern match – simple overlap with poet's common qaafiya? Not stored, so use 0 for now.
        # For a future upgrade, you could store top qaafiya patterns in stylistic_features.
        qaafiya_score = 0.0

        # 4. Vocabulary style – place holder (0.5)
        vocab_score = 0.5

        # Hybrid score
        hybrid = (0.6 * emb_sim) + (0.2 * radif_match) + (0.1 * qaafiya_score) + (0.1 * vocab_score)

        results.append({
            'poet_id': poet_id,
            'hybrid_similarity': hybrid,
            'components': {
                'embedding': round(emb_sim, 3),
                'radif_match': radif_match,
                'qaafiya': round(qaafiya_score, 3),
                'vocab': round(vocab_score, 3)
            }
        })

    results.sort(key=lambda x: x['hybrid_similarity'], reverse=True)
    return results[:3]