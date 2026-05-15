# modules/embeddings.py – Lightweight stub for Render free tier
# In lightweight mode, semantic search uses TF-IDF, not sentence-transformers
# This stub provides dummy embeddings for compatibility

import numpy as np

# Dummy 384-dim zero vector (same size as the original model)
DUMMY_EMBEDDING = [0.0] * 384


def generate_embedding(text):
    """
    Lightweight stub – returns a zero vector.
    In lightweight mode, actual semantic search is handled by TF‑IDF.
    """
    return DUMMY_EMBEDDING


def cosine_similarity(v1, v2):
    """Simple cosine similarity for two vectors."""
    if not v1 or not v2:
        return 0.0
    v1 = np.array(v1)
    v2 = np.array(v2)
    if np.linalg.norm(v1) == 0 or np.linalg.norm(v2) == 0:
        return 0.0
    return float(np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2)))


def normalize_urdu(text):
    """Simple normalization – removes extra spaces and punctuation."""
    if not text:
        return ""
    import re
    text = text.strip()
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'[،۔.!?]', '', text)
    return text


# ========== Dummy functions for compatibility with older code ==========
def get_model():
    """Dummy – returns None."""
    return None


def get_ghazal_lines(conn, text_id):
    """Dummy – returns empty list."""
    return []


def build_ghazal_embedding(lines):
    """Dummy – returns zero vector."""
    return np.zeros(384)


def update_ghazal_embedding(text_id):
    """Dummy – does nothing."""
    print(f"⚠️ Embedding update skipped in lightweight mode for ghazal {text_id}")
    return


def fast_similarity_search(query_vec, top_n=20):
    """Dummy – returns empty list."""
    return []


def predict_poet_by_similarity(input_text, top_n=3):
    """Dummy – uses lightweight poet prediction instead."""
    from models.ai_engine.poet_prediction_ai_v2 import predict_poet
    return predict_poet(input_text, top_n)
