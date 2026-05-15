# ============================================
# UCPC Lightweight Semantic Search
# TF-IDF Based Semantic Retrieval
# ============================================

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from models.base import get_db_connection

class LightweightSemanticEngine:
    def __init__(self):
        self.vectorizer = TfidfVectorizer(
            max_features=5000,
            ngram_range=(1, 2),
            min_df=2,
            max_df=0.95
        )
        self.df = None
        self.matrix = None
        self.loaded = False

    def load_data(self):
        if self.loaded:
            return
        print("📚 Loading semantic corpus...")
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT
                t.id,
                p.name,
                COALESCE(t.title_urdu, ''),
                STRING_AGG(
                    COALESCE(v.misra1_urdu, '') || ' ' ||
                    COALESCE(v.misra2_urdu, ''),
                    ' '
                )
            FROM texts t
            JOIN poets p ON t.poet_id = p.id
            LEFT JOIN verses v ON t.id = v.text_id
            WHERE t.form = 'ghazal'
            GROUP BY t.id, p.name, t.title_urdu
            LIMIT 3000
        """)
        rows = cur.fetchall()
        cur.close()
        conn.close()
        data = []
        for r in rows:
            data.append({
                "text_id": r[0],
                "poet": r[1],
                "title": r[2],
                "text": r[3] or ""
            })
        self.df = pd.DataFrame(data)
        if len(self.df) == 0:
            return
        self.matrix = self.vectorizer.fit_transform(self.df["text"])
        self.loaded = True
        print(f"✅ Semantic corpus loaded: {len(self.df)} ghazals")

semantic_engine = LightweightSemanticEngine()

def search_semantic(query, top_k=10):
    semantic_engine.load_data()
    if semantic_engine.df is None:
        return []
    q_vec = semantic_engine.vectorizer.transform([query])
    sims = cosine_similarity(q_vec, semantic_engine.matrix)[0]
    top_indices = np.argsort(sims)[::-1][:top_k]
    results = []
    for idx in top_indices:
        row = semantic_engine.df.iloc[idx]
        results.append({
            "text_id": int(row["text_id"]),
            "poet": row["poet"],
            "title": row["title"],
            "score": float(sims[idx])
        })
    return results
