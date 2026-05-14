"""
UCPC Semantic Search Engine v2
Research-grade hybrid retrieval system for Urdu Computational Philology.

Features:
- BM25 lexical retrieval
- SentenceTransformer embeddings (singleton, cached)
- Hybrid ranking
- Matla-aware scoring
- Intertextual reranking
- Persistent index caching
- Lazy loading (no heavy init on import)
"""

import os
import sys
import re
import pickle
import numpy as np

try:
    from rank_bm25 import BM25Okapi
except ImportError:
    print("⚠️ rank_bm25 not installed. Run: pip install rank_bm25")
    BM25Okapi = None

from sklearn.metrics.pairwise import cosine_similarity

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

from models.base import get_db_connection
from modules.intertextual_analysis import IntertextualAnalyzer


# ========== GLOBAL MODEL (loaded once, shared across all instances) ==========
_SENTENCE_MODEL = None

def get_sentence_model():
    """Singleton pattern for SentenceTransformer model (lazy loaded)."""
    global _SENTENCE_MODEL
    if _SENTENCE_MODEL is None:
        print("🔄 Loading SentenceTransformer model (one‑time, 2-3 minutes)...")
        from sentence_transformers import SentenceTransformer
        _SENTENCE_MODEL = SentenceTransformer(
            "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
        )
        print("✅ SentenceTransformer model loaded")
    return _SENTENCE_MODEL


# ========== CACHE CONFIGURATION ==========
CACHE_DIR = os.path.join(os.path.dirname(__file__), "cache")
CACHE_PATH = os.path.join(CACHE_DIR, "semantic_index.pkl")


class UrduTextPreprocessor:
    def normalize_urdu(self, text):
        if not text:
            return ""
        text = str(text)
        replacements = {"ي": "ی", "ك": "ک", "ة": "ہ", "أ": "ا", "إ": "ا", "آ": "آ"}
        for old, new in replacements.items():
            text = text.replace(old, new)
        text = re.sub(r"[^\u0600-\u06FF\s]", " ", text)
        text = re.sub(r"\s+", " ", text)
        return text.strip()


class UCPCHybridSemanticEngine:
    def __init__(self):
        self.preprocessor = UrduTextPreprocessor()
        self.intertextual = None  # Lazy load
        self.documents = []
        self.doc_vectors = None
        self.bm25 = None
        self._initialized = False

    def _get_intertextual(self):
        """Lazy load IntertextualAnalyzer."""
        if self.intertextual is None:
            self.intertextual = IntertextualAnalyzer()
        return self.intertextual

    def _ensure_initialized(self):
        """Load cache or build index only when needed."""
        if self._initialized:
            return
        self._initialized = True
        
        if not self._load_cached_index():
            print("⚠️ No cache found. Building index from scratch...")
            self.build_index()

    def _load_cached_index(self):
        """Load pre-computed index from cache file."""
        if not os.path.exists(CACHE_PATH):
            return False
        
        try:
            print("📀 Loading cached semantic index...")
            with open(CACHE_PATH, "rb") as f:
                cache = pickle.load(f)
            
            self.documents = cache["documents"]
            self.doc_vectors = cache["embeddings"]
            self.bm25 = cache["bm25"]
            
            print(f"✅ Loaded {len(self.documents)} documents from cache")
            return True
        except Exception as e:
            print(f"⚠️ Failed to load cache: {e}")
            return False

    def normalize(self, text):
        return self.preprocessor.normalize_urdu(text)

    def tokenize(self, text):
        text = self.normalize(text)
        return text.split()

    def load_corpus(self):
        """Load ghazals from database."""
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT t.id, t.title_urdu, t.text_urdu, t.normalized_text, t.matla, p.name, p.name_urdu
            FROM texts t
            JOIN poets p ON t.poet_id = p.id
            WHERE t.text_urdu IS NOT NULL 
              AND t.form = 'ghazal' 
              AND (t.is_deleted = FALSE OR t.is_deleted IS NULL)
        """)
        rows = cur.fetchall()
        cur.close()
        conn.close()
        
        docs = []
        for r in rows:
            if hasattr(r, "keys"):
                doc = {
                    "text_id": r["id"],
                    "title": r["title_urdu"],
                    "text": r["normalized_text"] or r["text_urdu"],
                    "matla": r["matla"] or "",
                    "poet": r["name"],
                    "poet_urdu": r["name_urdu"]
                }
            else:
                doc = {
                    "text_id": r[0],
                    "title": r[1],
                    "text": r[3] or r[2],
                    "matla": r[4] or "",
                    "poet": r[5],
                    "poet_urdu": r[6]
                }
            docs.append(doc)
        
        self.documents = docs
        print(f"✅ Loaded {len(self.documents)} ghazals")

    def build_bm25(self):
        """Build BM25 lexical index."""
        if BM25Okapi is None:
            print("⚠️ BM25 not available. Install rank_bm25")
            self.bm25 = None
            return
        
        tokenized = [self.tokenize(doc["text"]) for doc in self.documents]
        self.bm25 = BM25Okapi(tokenized)
        print("✅ BM25 index built")

    def build_embeddings(self):
        """Generate sentence embeddings using singleton model."""
        texts = [doc["text"] for doc in self.documents]
        model = get_sentence_model()  # Singleton pattern (lazy)
        self.doc_vectors = model.encode(texts, show_progress_bar=True, convert_to_numpy=True)
        print("✅ Embeddings generated")

    def build_index(self):
        """Build full index (corpus + BM25 + embeddings)."""
        print("🔄 Building semantic index...")
        self.load_corpus()
        self.build_bm25()
        self.build_embeddings()
        print("✅ Semantic index built")

    def matla_boost(self, query, matla):
        if not matla:
            return 0.0
        query = self.normalize(query)
        matla = self.normalize(matla)
        if query in matla:
            return 0.25
        similarity = self._get_intertextual().sequence_similarity(query, matla)
        return similarity * 0.15

    def search(self, query, top_n=10):
        """Hybrid semantic search (lazy initialization)."""
        self._ensure_initialized()
        
        if not self.documents:
            return []
        
        query = self.normalize(query)
        tokenized_query = self.tokenize(query)
        
        # BM25 scores
        if self.bm25:
            bm25_scores = self.bm25.get_scores(tokenized_query)
        else:
            bm25_scores = [0] * len(self.documents)
        
        # Semantic scores
        model = get_sentence_model()
        query_vector = model.encode([query])
        semantic_scores = cosine_similarity(query_vector, self.doc_vectors)[0]
        
        results = []
        for idx, doc in enumerate(self.documents):
            bm25_score = float(bm25_scores[idx])
            semantic_score = float(semantic_scores[idx])
            normalized_bm25 = min(bm25_score / 20, 1.0)
            hybrid_score = semantic_score * 0.60 + normalized_bm25 * 0.40
            hybrid_score += self.matla_boost(query, doc["matla"])
            
            intertext = self._get_intertextual().analyze(query, doc["text"][:800])
            hybrid_score += intertext["overall_intertextuality"] * 0.15
            
            results.append({
                "text_id": doc["text_id"],
                "title": doc["title"],
                "poet": doc["poet"],
                "poet_urdu": doc["poet_urdu"],
                "matla": doc["matla"],
                "score": round(hybrid_score, 4),
                "semantic_score": round(semantic_score, 4),
                "bm25_score": round(normalized_bm25, 4),
                "intertextuality": intertext["overall_intertextuality"],
                "shared_imagery": intertext["shared_imagery"]
            })
        
        results = sorted(results, key=lambda x: x["score"], reverse=True)
        return results[:top_n]

    def influence_search(self, query, threshold=0.60):
        results = self.search(query, top_n=50)
        return [r for r in results if r["intertextuality"] >= threshold]

    def find_similar_by_id(self, text_id, top_n=10):
        self._ensure_initialized()
        target = next((doc for doc in self.documents if doc["text_id"] == text_id), None)
        if not target:
            return []
        return self.search(target["text"], top_n=top_n)


# ========== LAZY SINGLETON INSTANCE ==========
_semantic_engine = None

def get_semantic_engine():
    """Lazy-loaded singleton semantic engine (no heavy init on import)."""
    global _semantic_engine
    if _semantic_engine is None:
        print("🔄 Initializing UCPC Semantic Engine (lazy load)...")
        _semantic_engine = UCPCHybridSemanticEngine()
    return _semantic_engine


def search_semantic(query, top_n=10):
    """Convenience function for semantic search."""
    return get_semantic_engine().search(query, top_n=top_n)


if __name__ == "__main__":
    query = "دل میں اک حسرت سی رہ گئی ہے"
    results = search_semantic(query, top_n=3)
    print("\nUCPC Semantic Search Test")
    print("=" * 50)
    for r in results:
        print(f"{r['poet']}: {r['score']}")
        print(f"  {r['matla'][:100]}...")
        print("-" * 30)
