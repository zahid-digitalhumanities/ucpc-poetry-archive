"""
UCPC Semantic Index Builder
Run this script ONCE to build and cache the semantic index.
"""

import pickle
import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

from semantic.semantic_search_v2 import UCPCHybridSemanticEngine

def main():
    print("=" * 60)
    print("UCPC Semantic Index Builder")
    print("=" * 60)
    
    print("\n🔄 Building semantic index (one‑time operation)...")
    print("   This may take 2-3 minutes for 5000+ ghazals...")
    
    engine = UCPCHybridSemanticEngine()
    engine.build_index()
    
    # Save cache
    SAVE_DIR = os.path.join(os.path.dirname(__file__), "cache")
    os.makedirs(SAVE_DIR, exist_ok=True)
    SAVE_PATH = os.path.join(SAVE_DIR, "semantic_index.pkl")
    
    with open(SAVE_PATH, "wb") as f:
        pickle.dump({
            "documents": engine.documents,
            "embeddings": engine.doc_vectors,
            "bm25": engine.bm25
        }, f)
    
    print(f"\n✅ Index saved to {SAVE_PATH}")
    print(f"   Size: {os.path.getsize(SAVE_PATH) / 1024 / 1024:.1f} MB")
    
    print("\n🚀 You can now start Flask: python app.py")

if __name__ == "__main__":
    main()