from collections import defaultdict
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

def predict_poet(text_id, top_n=3, prefilter_n=50):
    conn = get_db_connection()
    cur = conn.cursor()

    # Get target embedding
    cur.execute("SELECT embedding_vector FROM ghazal_embeddings WHERE text_id = %s", (text_id,))
    target_row = cur.fetchone()
    if not target_row:
        return []
    target_emb = target_row['embedding_vector']
    if isinstance(target_emb, str):
        target_emb = json.loads(target_emb)

    # Get all other ghazals with embeddings and poet info
    cur.execute("""
        SELECT t.id, t.poet_id, p.name, g.embedding_vector
        FROM texts t
        JOIN poets p ON t.poet_id = p.id
        JOIN ghazal_embeddings g ON t.id = g.text_id
        WHERE t.id != %s
    """, (text_id,))
    rows = cur.fetchall()

    # Stage 1: Fast embedding prefilter
    candidates = []
    for r in rows:
        cand_emb = r['embedding_vector']
        if isinstance(cand_emb, str):
            cand_emb = json.loads(cand_emb)
        sim = cosine_similarity(target_emb, cand_emb)
        candidates.append((r['id'], r['poet_id'], r['name'], sim))

    candidates.sort(key=lambda x: x[3], reverse=True)
    top_candidates = candidates[:prefilter_n]

    # Stage 2: Explainable reranking
    poet_scores = defaultdict(list)   # list of scores per poet
    poet_explanations = defaultdict(list)  # store explanations (for display)

    for cand_id, poet_id, poet_name, emb_score in top_candidates:
        exp = explain_similarity(text_id, cand_id)
        score = exp.get('score', 0)
        if score <= 0:
            continue
        poet_scores[poet_id].append(score)
        poet_explanations[poet_id].append({
            'ghazal_id': cand_id,
            'score': score,
            'explanation': exp.get('explanation', [])
        })

    # Average scores per poet
    poet_avg = {pid: sum(scores)/len(scores) for pid, scores in poet_scores.items()}

    # Sort by average score
    ranked = sorted(poet_avg.items(), key=lambda x: x[1], reverse=True)

    results = []
    for poet_id, avg_score in ranked[:top_n]:
        cur.execute("SELECT name FROM poets WHERE id = %s", (poet_id,))
        poet_name = cur.fetchone()['name']

        # Get top 2 examples for this poet (by score)
        examples = sorted(poet_explanations[poet_id], key=lambda x: x['score'], reverse=True)[:2]

        # Build a single explanation (most important features)
        # Use the first example's explanation (or combine unique lines)
        if examples:
            # Extract the most informative line (first line of explanation is usually the semantic)
            main_explanation = examples[0]['explanation'][0] if examples[0]['explanation'] else "Similar ghazal found"
        else:
            main_explanation = "No detailed explanation"

        results.append({
            'poet_id': poet_id,
            'poet_name': poet_name,
            'score': round(avg_score, 3),   # between 0 and 1
            'examples': examples,
            'explanation_summary': main_explanation
        })

    cur.close()
    conn.close()
    return results