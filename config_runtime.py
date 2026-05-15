# ============================================
# UCPC Runtime Configuration
# Lightweight Production Settings
# ============================================

import os

ENVIRONMENT = os.getenv("FLASK_ENV", "production")
LIGHTWEIGHT_MODE = os.getenv("LIGHTWEIGHT_MODE", "true").lower() == "true"
ENABLE_TRANSFORMERS = os.getenv("ENABLE_TRANSFORMERS", "false").lower() == "true"
ENABLE_SENTENCE_BERT = os.getenv("ENABLE_SENTENCE_BERT", "false").lower() == "true"
ENABLE_HEAVY_EMBEDDINGS = os.getenv("ENABLE_HEAVY_EMBEDDINGS", "false").lower() == "true"
SEMANTIC_TOP_K = int(os.getenv("SEMANTIC_TOP_K", 10))
FUZZY_MATCH_THRESHOLD = int(os.getenv("FUZZY_MATCH_THRESHOLD", 55))
ENABLE_POET_PREDICTION = os.getenv("ENABLE_POET_PREDICTION", "true").lower() == "true"
MAX_POET_RESULTS = int(os.getenv("MAX_POET_RESULTS", 5))
DISABLE_TORCH = os.getenv("DISABLE_TORCH", "true").lower() == "true"
DISABLE_GPU = True
ENABLE_CACHE = True
CACHE_SIZE = int(os.getenv("CACHE_SIZE", 200))
DEBUG_RUNTIME = os.getenv("DEBUG_RUNTIME", "false").lower() == "true"

print("="*60)
print("🚀 UCPC Runtime Configuration Loaded")
print(f"Environment: {ENVIRONMENT}")
print(f"Lightweight Mode: {LIGHTWEIGHT_MODE}")
print(f"Poet Prediction Enabled: {ENABLE_POET_PREDICTION}")
print("="*60)
