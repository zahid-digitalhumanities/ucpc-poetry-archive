# models/similarity_model.py - Free tier optimized version
import json
import numpy as np
from models.base import get_db_connection

# DISABLED for free tier - explainability module requires ML packages
# from modules.explainability import explain_similarity

def cosine_similarity(vec1, vec2):
    """Compute cosine similarity between two vectors."""
    v1 = np.array(vec1)
    v2 = np.array(vec2)
    if v1.size == 0 or v2.size == 0:
        return 0.0
    norm_product = np.linalg.norm(v1) * np.linalg.norm(v2)
    if norm_product == 0:
        return 0.0
    return float(np.dot(v1, v2) / norm_product)

def find_similar_ghazals(text_id, top_n=10, prefilter_n=50):
    """
    Find similar ghazals using keyword-based matching.
    Falls back to basic similarity when embeddings are not available.
    """
    conn = get_db_connection()
    cur = conn.cursor()
    
    # First, try to get target ghazal text
    cur.execute("""
        SELECT t.id, t.title_urdu, t.text_urdu, p.name as poet_name
        FROM texts t
        JOIN poets p ON t.poet_id = p.id
        WHERE t.id = %s
    """, (text_id,))
    target = cur.fetchone()
    
    if not target:
        cur.close()
        conn.close()
        return []
    
    # Get target text for keyword matching
    target_text = target.get('text_urdu', '') if isinstance(target, dict) else target[2]
    target_poet = target.get('poet_name', '') if isinstance(target, dict) else target[3]
    
    # Get all other ghazals for comparison
    cur.execute("""
        SELECT t.id, t.title_urdu, t.text_urdu, p.name as poet_name
        FROM texts t
        JOIN poets p ON t.poet_id = p.id
        WHERE t.id != %s AND t.form = 'ghazal'
        LIMIT 200
    """, (text_id,))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    
    # Simple keyword-based similarity scoring
    results = []
    target_keywords = set(target_text.split()[:50]) if target_text else set()
    
    for row in rows:
        if isinstance(row, dict):
            cand_text = row.get('text_urdu', '')
            cand_poet = row.get('poet_name', '')
            cand_id = row.get('id')
            cand_title = row.get('title_urdu', '')
        else:
            cand_id = row[0]
            cand_title = row[1] or ''
            cand_text = row[2] or ''
            cand_poet = row[3] or ''
        
        # Calculate keyword overlap
        cand_keywords = set(cand_text.split()[:50]) if cand_text else set()
        
        if target_keywords and cand_keywords:
            overlap = len(target_keywords.intersection(cand_keywords))
            union = len(target_keywords.union(cand_keywords))
            keyword_score = overlap / union if union > 0 else 0
        else:
            keyword_score = 0
        
        # Bonus for same poet
        poet_bonus = 0.15 if cand_poet == target_poet else 0
        
        final_score = keyword_score * 0.7 + poet_bonus
        
        results.append({
            'text_id': cand_id,
            'similarity': round(min(final_score, 1.0), 3),
            'explanation': {
                'embedding_score': round(keyword_score, 3),
                'breakdown': {
                    'keyword_match': round(keyword_score, 3),
                    'poet_bonus': poet_bonus,
                    'radif': 0,
                    'qaafiya': 0,
                    'theme': 0
                },
                'explanation_text': f"Similarity based on keyword overlap and poet match (embeddings disabled on free tier)"
            }
        })
    
    results.sort(key=lambda x: x['similarity'], reverse=True)
    return results[:top_n]
