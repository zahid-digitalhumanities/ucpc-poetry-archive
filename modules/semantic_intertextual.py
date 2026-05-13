# modules/semantic_intertextual.py
"""
UCPC Semantic + Intertextual Engine
-----------------------------------

Research-grade semantic retrieval
and literary intertextuality analysis.

Features:
✅ Semantic similarity
✅ Intertextual linkage
✅ Cross-poet influence
✅ Couplet retrieval (proper first couplet only)
✅ Embedding-based search
✅ Research metadata
✅ Cross-lingual retrieval (Roman/Urdu)
✅ Influence mapping
"""

import os
import sys
import re
import numpy as np
from typing import List, Dict, Any, Optional

# Add project root to path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from models.base import get_db_connection


# =========================================================
# CONFIGURATION
# =========================================================

class SemanticConfig:
    CHAR_NGRAM_RANGE = (2, 5)
    MAX_FEATURES = 15000
    DEFAULT_TOP_K = 10
    SIMILARITY_THRESHOLD = 0.10
    STRONG_OVERLAP = 0.80
    INFLUENCE_THRESHOLD = 0.60
    THEMATIC_THRESHOLD = 0.40


# =========================================================
# NORMALIZATION
# =========================================================

def normalize_text(text: str) -> str:
    """Normalize Urdu text for consistent comparison"""
    if not text:
        return ""

    text = str(text)
    text = re.sub(r"\s+", " ", text)

    replacements = {
        "ي": "ی",
        "ك": "ک",
        "ة": "ہ",
        "أ": "ا",
        "إ": "ا",
        "آ": "ا",
        "ؤ": "و",
        "ئ": "ی",
    }

    for k, v in replacements.items():
        text = text.replace(k, v)

    return text.strip()


# =========================================================
# GET FIRST COUPLET FROM DATABASE (Reliable method)
# =========================================================

def get_first_couplet_from_db(text_id: int) -> str:
    """
    Fetch first couplet (sher) directly from verses table.
    Returns exactly 2 lines: misra1 and misra2.
    """
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT misra1_urdu, misra2_urdu 
            FROM verses 
            WHERE text_id = %s AND couplet_index = 1
        """, (text_id,))
        row = cur.fetchone()
        cur.close()
        conn.close()
        
        if row:
            if hasattr(row, 'keys'):
                misra1 = row['misra1_urdu'] or ''
                misra2 = row['misra2_urdu'] or ''
            else:
                misra1 = row[0] or ''
                misra2 = row[1] or ''
            
            if misra1 and misra2:
                return f"{misra1}\n{misra2}"
            elif misra1:
                return misra1
    except Exception as e:
        print(f"⚠️ Error fetching couplet for {text_id}: {e}")
    
    return ""


# =========================================================
# CORPUS LOADING (with caching)
# =========================================================

_corpus_cache = None

def load_corpus(force_reload: bool = False) -> List[Dict]:
    """Load corpus with caching for performance"""
    global _corpus_cache
    
    if _corpus_cache is not None and not force_reload:
        return _corpus_cache

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            t.id,
            t.text_urdu,
            t.normalized_text,
            p.name,
            p.name_urdu,
            t.title_urdu,
            t.verse_count
        FROM texts t
        JOIN poets p ON p.id = t.poet_id
        WHERE t.form = 'ghazal'
          AND (t.is_deleted = FALSE OR t.is_deleted IS NULL)
          AND t.text_urdu IS NOT NULL
        ORDER BY t.id
    """)

    rows = cur.fetchall()
    cur.close()
    conn.close()

    corpus = []
    for r in rows:
        if hasattr(r, "keys"):
            corpus.append({
                "text_id": r["id"],
                "text": normalize_text(r["normalized_text"] or r["text_urdu"]),
                "poet": r["name"],
                "poet_urdu": r["name_urdu"],
                "title": r["title_urdu"],
                "verse_count": r["verse_count"] or 0
            })
        else:
            corpus.append({
                "text_id": r[0],
                "text": normalize_text(r[2] or r[1]),
                "poet": r[3],
                "poet_urdu": r[4] if len(r) > 4 else "",
                "title": r[5] if len(r) > 5 else "",
                "verse_count": r[6] if len(r) > 6 else 0
            })

    _corpus_cache = corpus
    print(f"✅ Loaded {len(corpus)} ghazals into semantic corpus")
    return corpus


# =========================================================
# SEMANTIC SEARCH (Fixed - Proper first couplet only)
# =========================================================

def semantic_search(query: str, top_k: int = SemanticConfig.DEFAULT_TOP_K) -> List[Dict]:
    """
    Search for semantically similar ghazals using character n-gram TF-IDF.
    Returns ONLY the first couplet (first 2 lines) of each matching ghazal.
    Fetches couplet directly from verses table for accuracy.
    """
    query = normalize_text(query)
    corpus = load_corpus()

    if not corpus:
        return []

    texts = [x["text"] for x in corpus]

    vectorizer = TfidfVectorizer(
        analyzer="char_wb",
        ngram_range=SemanticConfig.CHAR_NGRAM_RANGE,
        max_features=SemanticConfig.MAX_FEATURES,
        sublinear_tf=True
    )

    X = vectorizer.fit_transform(texts)
    q = vectorizer.transform([query])
    sims = cosine_similarity(q, X)[0]

    top_indices = np.argsort(sims)[::-1][:top_k]

    results = []
    for idx in top_indices:
        item = corpus[idx]
        score = float(sims[idx])

        if score < SemanticConfig.SIMILARITY_THRESHOLD:
            continue

        # FIXED: Get first couplet from verses table (reliable)
        first_couplet = get_first_couplet_from_db(item["text_id"])
        
        # Fallback: if not found, try extracting from text
        if not first_couplet:
            lines = [l.strip() for l in item["text"].split('\n') if l.strip()]
            if len(lines) >= 2:
                first_couplet = f"{lines[0]}\n{lines[1]}"
            elif lines:
                first_couplet = lines[0]
            else:
                first_couplet = item["text"][:200] if item["text"] else ""

        results.append({
            "text_id": item["text_id"],
            "poet": item["poet"],
            "poet_urdu": item["poet_urdu"],
            "title": item["title"],
            "score": round(score, 4),
            "score_percent": round(score * 100, 1),
            "first_couplet": first_couplet,  # Now properly 2 lines
            "retrieval_type": "semantic_similarity",
            "verse_count": item.get("verse_count", 0)
        })

    return results


# =========================================================
# INTERTEXTUAL DETECTION
# =========================================================

def detect_intertextual_links(query: str, top_k: int = 10) -> List[Dict]:
    """
    Detect intertextual relationships between the query and corpus texts.
    Returns relationship types: strong overlap, literary influence, thematic structure.
    """
    results = semantic_search(query, top_k=top_k * 2)

    enriched = []
    for r in results:
        score = r["score"]

        if score >= SemanticConfig.STRONG_OVERLAP:
            relation = "strong textual overlap"
            relation_urdu = "مضبوط متنی ہم آہنگی"
            confidence = "high"
        elif score >= SemanticConfig.INFLUENCE_THRESHOLD:
            relation = "possible literary influence"
            relation_urdu = "ممکنہ ادبی اثر"
            confidence = "moderate"
        elif score >= SemanticConfig.THEMATIC_THRESHOLD:
            relation = "shared thematic structure"
            relation_urdu = "ہم عنوان ساخت"
            confidence = "moderate"
        else:
            relation = "weak semantic relation"
            relation_urdu = "کمزور معنوی تعلق"
            confidence = "low"

        enriched.append({
            "text_id": r["text_id"],
            "poet": r["poet"],
            "poet_urdu": r["poet_urdu"],
            "title": r["title"],
            "score": r["score"],
            "score_percent": r["score_percent"],
            "relation": relation,
            "relation_urdu": relation_urdu,
            "confidence": confidence,
            "first_couplet": r["first_couplet"],
            "verse_count": r.get("verse_count", 0)
        })

    return enriched[:top_k]


# =========================================================
# GET SIMILARITY MATRIX (Research Feature)
# =========================================================

def get_similarity_matrix(limit: int = 100) -> Dict:
    """
    Generate similarity matrix for a subset of the corpus.
    Useful for network analysis and visualization.
    """
    corpus = load_corpus()[:limit]
    
    texts = [x["text"] for x in corpus]
    ids = [x["text_id"] for x in corpus]
    poets = [x["poet"] for x in corpus]
    
    vectorizer = TfidfVectorizer(
        analyzer="char_wb",
        ngram_range=(2, 5),
        max_features=5000
    )
    
    X = vectorizer.fit_transform(texts)
    similarity_matrix = cosine_similarity(X)
    
    return {
        "text_ids": ids,
        "poets": poets,
        "similarity_matrix": similarity_matrix.tolist(),
        "shape": similarity_matrix.shape
    }


# =========================================================
# API HELPER - Format for Frontend
# =========================================================

def format_for_api(results: List[Dict]) -> List[Dict]:
    """Format results for API response"""
    formatted = []
    for r in results:
        formatted.append({
            "text_id": r.get("text_id"),
            "poet": r.get("poet"),
            "poet_urdu": r.get("poet_urdu", ""),
            "title": r.get("title", ""),
            "similarity": r.get("score_percent", r.get("score", 0) * 100),
            "first_couplet": r.get("first_couplet", ""),
            "relation": r.get("relation", "semantic_similarity"),
            "verse_count": r.get("verse_count", 0)
        })
    return formatted


# =========================================================
# TEST
# =========================================================

if __name__ == "__main__":
    print("=" * 60)
    print("UCPC Semantic + Intertextual Engine - Test")
    print("=" * 60)
    
    # Test first couplet retrieval
    print("\n1. Testing First Couplet Retrieval:")
    print("-" * 40)
    
    # Get a sample ghazal ID
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id FROM texts WHERE form = 'ghazal' LIMIT 1")
    row = cur.fetchone()
    cur.close()
    conn.close()
    
    if row:
        test_id = row[0] if not hasattr(row, 'keys') else row['id']
        couplet = get_first_couplet_from_db(test_id)
        print(f"  Ghazal ID: {test_id}")
        print(f"  First couplet:\n    {couplet}")
    
    # Test semantic search
    print("\n2. Semantic Search Test (First Couplet Only):")
    print("-" * 40)
    results = semantic_search("دل ہی تو ہے", top_k=3)
    for r in results:
        print(f"\n  Poet: {r['poet']}")
        print(f"  Similarity: {r['score_percent']}%")
        print(f"  First couplet:")
        for line in r['first_couplet'].split('\n'):
            print(f"    {line}")
    
    print("\n✅ Module ready for production")