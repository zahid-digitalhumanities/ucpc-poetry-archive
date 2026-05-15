# ============================================
# UCPC Lightweight Memory-Safe Mode
# Render Free Tier Optimization
# ============================================

import os
import gc
import warnings

os.environ["OMP_NUM_THREADS"] = "1"
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["VECLIB_MAXIMUM_THREADS"] = "1"
os.environ["NUMEXPR_NUM_THREADS"] = "1"
os.environ["CUDA_VISIBLE_DEVICES"] = ""
os.environ["TOKENIZERS_PARALLELISM"] = "false"
os.environ["PYTORCH_ENABLE_MPS_FALLBACK"] = "1"

warnings.filterwarnings("ignore")

def cleanup_memory():
    gc.collect()

def safe_import(module_name):
    try:
        return __import__(module_name)
    except Exception as e:
        print(f"⚠️ Failed to import {module_name}: {e}")
        return None

def runtime_status():
    return {"mode": "LIGHTWEIGHT", "gpu": False, "threads": 1, "memory_safe": True}

print("="*60)
print("🧠 UCPC Lightweight Mode Activated")
print("✅ GPU Disabled | Torch Safe Mode | Single Thread Mode")
print("="*60)
