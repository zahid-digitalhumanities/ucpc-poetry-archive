# startup.py - MUST be first import in app.py
import os
import sys

# CRITICAL: Disable all heavy model imports
os.environ["DISABLE_SEMANTIC"] = "true"
os.environ["DISABLE_POET_PREDICTOR"] = "true"
os.environ["DISABLE_HEAVY_MODELS"] = "true"

# Limit threads to prevent explosion
os.environ["TOKENIZERS_PARALLELISM"] = "false"
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["NUMEXPR_NUM_THREADS"] = "1"

# Force garbage collection
import gc
gc.collect()

print("✅ Emergency startup patch applied - heavy models disabled")