# modules/poet_classifier.py
import pickle
import json
import os
from models.base import get_db_connection

_model = None
_label_encoder = None

def _load_model():
    global _model, _label_encoder
    if _model is None:
        model_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'models', 'poet_classifier.pkl')
        if not os.path.exists(model_path):
            return None, None
        with open(model_path, 'rb') as f:
            _model, _label_encoder = pickle.load(f)
    return _model, _label_encoder

def hash_str(s, n_bins=100):
    if not s:
        return 0
    return hash(s) % n_bins

def get_feature_name(index):
    """Return human-readable name for a given feature index (0‑390)."""
    if index < 384:
        # Group embedding dimensions into 10 buckets
        bucket = index // 38  # 38*10 = 380, leaving 4 extra, but fine
        bucket_names = [
            "Vocabulary richness", "Syntactic patterns", "Rhythmic structure",
            "Morphological features", "Phonetic style", "Lexical density",
            "Poetic imagery", "Repetition patterns", "Syllable distribution", "Emotional tone"
        ]
        return bucket_names[min(bucket, 9)]
    else:
        # Manual features (indices 384–390)
        manual = {
            384: "Radif (refrain) pattern",
            385: "First Qaafiya (rhyme) pattern",
            386: "Second Qaafiya pattern",
            387: "Third Qaafiya pattern",
            388: "Meter (behr) pattern",
            389: "Theme category",
            390: "Number of verses"
        }
        return manual.get(index, f"Feature {index}")

def get_global_feature_importances(model, top_k=3):
    """Return top-k global feature importances with human-readable names."""
    importances = model.feature_importances_
    top_indices = importances.argsort()[-top_k:][::-1]
    result = []
    for idx in top_indices:
        result.append({
            'name': get_feature_name(idx),
            'importance': float(importances[idx])
        })
    return result

def predict_poet_by_id(text_id, use_cache=True):
    if use_cache:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT top3, feature_contributions FROM poet_predictions WHERE text_id = %s", (text_id,))
        cached = cur.fetchone()
        cur.close()
        conn.close()
        if cached and cached['top3']:
            return cached['top3']

    model, le = _load_model()
    if model is None:
        return []

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT t.poet_id,
               pf.radif, pf.qaafiya, pf.meter, pf.theme,
               g.embedding_vector
        FROM texts t
        LEFT JOIN poetic_features pf ON t.id = pf.text_id
        LEFT JOIN ghazal_embeddings g ON t.id = g.text_id
        WHERE t.id = %s
    """, (text_id,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    if not row:
        return []

    radif = row['radif'] or ''
    qaafiya_list = row['qaafiya'] or []
    meter = row['meter'] or ''
    theme = row['theme'] or ''
    emb = row['embedding_vector']
    if isinstance(emb, str):
        try:
            emb = json.loads(emb)
        except:
            emb = None
    if emb is None or len(emb) != 384:
        emb = [0.0] * 384

    # Build feature vector (391 features total)
    features = list(emb)
    features.append(hash_str(radif, 100))
    q_hashes = [hash_str(w, 100) for w in qaafiya_list[:3]]
    while len(q_hashes) < 3:
        q_hashes.append(0)
    features.extend(q_hashes)
    features.append(hash_str(meter, 50))
    features.append(hash_str(theme, 10))
    features.append(len(qaafiya_list))

    try:
        proba = model.predict_proba([features])[0]
        top_indices = proba.argsort()[-3:][::-1]
        results = []
        # Get global top features (same for all predictions)
        global_features = get_global_feature_importances(model, top_k=3)
        for idx in top_indices:
            poet_id = int(le.inverse_transform([idx])[0])
            conn2 = get_db_connection()
            cur2 = conn2.cursor()
            cur2.execute("SELECT name, name_urdu FROM poets WHERE id = %s", (poet_id,))
            poet_row = cur2.fetchone()
            cur2.close()
            conn2.close()
            if poet_row:
                results.append({
                    'poet_id': poet_id,
                    'name': poet_row['name'],
                    'name_urdu': poet_row['name_urdu'],
                    'probability': float(proba[idx]),
                    'features': global_features
                })

        # Cache the results
        if use_cache and results:
            predicted_poet_id = results[0]['poet_id']
            confidence = results[0]['probability']
            conn3 = get_db_connection()
            cur3 = conn3.cursor()
            cur3.execute("""
                INSERT INTO poet_predictions (text_id, predicted_poet_id, confidence, top3, feature_contributions)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (text_id) DO UPDATE SET
                    predicted_poet_id = EXCLUDED.predicted_poet_id,
                    confidence = EXCLUDED.confidence,
                    top3 = EXCLUDED.top3,
                    feature_contributions = EXCLUDED.feature_contributions,
                    updated_at = NOW()
            """, (text_id, predicted_poet_id, confidence,
                  json.dumps(results),
                  json.dumps([global_features])))
            conn3.commit()
            cur3.close()
            conn3.close()

        return results
    except Exception as e:
        print(f"Prediction error for text_id {text_id}: {e}")
        import traceback
        traceback.print_exc()
        return []