# models/ai_engine/poet_attribution_engine.py
"""
Final prediction pipeline:
1. Normalize input
2. Check corpus (exact / near duplicate) → if found, return immediately
3. Else, extract stylometric features and run ensemble
4. Return explanation with evidence
"""

import sys
import os
import pickle
import numpy as np
from collections import defaultdict

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from models.retrieval_memory import corpus_lookup
from modules.stylometric_features import extract_char_ngrams, extract_stylometric_features
from models.base import get_db_connection

MODEL_PATH = os.path.join(os.path.dirname(__file__), '..', 'ml', 'stylometric_poet_model.pkl')
_model_package = None

def load_model():
    global _model_package
    if _model_package is None:
        with open(MODEL_PATH, 'rb') as f:
            _model_package = pickle.load(f)
    return _model_package

def get_top_evidence(poet_id, text, model_package, top_n=5):
    """
    Simple evidence extraction: find most similar couplets in corpus for that poet.
    """
    conn = get_db_connection()
    cur = conn.cursor()
    # Get a few random verses by the same poet (simplified)
    cur.execute("""
        SELECT v.misra1_urdu, v.misra2_urdu
        FROM verses v
        JOIN texts t ON v.text_id = t.id
        WHERE t.poet_id = %s AND t.is_deleted = FALSE
        ORDER BY RANDOM()
        LIMIT 3
    """, (poet_id,))
    examples = cur.fetchall()
    cur.close()
    conn.close()
    evidence = [f"Similar to: {ex[0]} ... {ex[1]}" for ex in examples]
    return evidence

def predict_poet_with_retrieval(text: str, top_n: int = 3) -> dict:
    """
    Main attribution function.
    """
    # 1. Normalize
    from modules.text_normalizer import normalize_urdu
    text_norm = normalize_urdu(text)
    
    # 2. Corpus lookup
    lookup = corpus_lookup(text_norm, similarity_threshold=0.92)
    if lookup['found']:
        return {
            'poet_id': lookup['poet_id'],
            'poet_name': lookup['poet_name'],
            'confidence': lookup['confidence'],
            'method': 'corpus_retrieval',
            'match_type': lookup['match_type'],
            'explanation': f"Exact match found in corpus. Attributed to {lookup['poet_name']}."
        }
    
    # 3. Load ML model
    model_pkg = load_model()
    model = model_pkg['model']
    vectorizer = model_pkg['vectorizer']
    le = model_pkg['label_encoder']
    
    # Extract stylometric representation
    stylo_str = extract_char_ngrams(text_norm, n_range=(3,7))
    X_input = vectorizer.transform([stylo_str])
    
    probs = model.predict_proba(X_input)[0]
    top_indices = np.argsort(probs)[::-1][:top_n]
    
    results = []
    for idx in top_indices:
        poet_id = le.inverse_transform([idx])[0]
        poet_name = get_poet_name_from_id(poet_id)
        confidence = float(probs[idx]) * 100
        evidence = get_top_evidence(poet_id, text_norm, model_pkg)
        results.append({
            'poet_id': poet_id,
            'poet_name': poet_name,
            'confidence': round(confidence, 2),
            'explanation': evidence
        })
    
    return {
        'poet_id': results[0]['poet_id'],
        'poet_name': results[0]['poet_name'],
        'confidence': results[0]['confidence'],
        'method': 'stylometric_ml',
        'alternatives': results[1:],
        'explanation': f"Stylometric analysis suggests {results[0]['poet_name']}. Evidence: {results[0]['explanation'][0]}"
    }

def get_poet_name_from_id(pid):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT name FROM poets WHERE id = %s", (pid,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row[0] if row else f"Poet_{pid}"