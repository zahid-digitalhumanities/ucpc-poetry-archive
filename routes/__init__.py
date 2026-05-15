# routes/__init__.py
# Lightweight version – only essential routes for public poetry archive

# Core routes (always needed)
from .main_routes import main_bp
from .poets_routes import poets_bp
from .ghazals_routes import ghazals_bp
from .search_routes import search_bp
from .bulk_routes import bulk_bp

# Optional: Add these only if they exist and are lightweight
try:
    from .ingest_routes import ingest_bp
except ImportError:
    ingest_bp = None

try:
    from .corpus_routes import corpus_bp
except ImportError:
    corpus_bp = None

try:
    from .integrity_routes import integrity_bp
except ImportError:
    integrity_bp = None

try:
    from .listen_routes import listen_bp
except ImportError:
    listen_bp = None

# ============================================
# IMPORTANT: DO NOT import these heavy routes
# They cause memory issues on Render free tier
# ============================================

# from .ai_routes import ai_bp
# from .ask_ucpc_route import ask_bp
# from .ask_ucpc_index import ask_ucpc_bp
# from .semantic_routes import semantic_bp
# from .research_dashboard import research_dashboard_bp
# from .dh_advanced import dh_bp
# from .research_validation_routes import validation_bp
# from .similarity_route import similarity_bp
# from .insights_routes import insights_bp

__all__ = [
    'main_bp',
    'poets_bp',
    'ghazals_bp',
    'search_bp',
    'bulk_bp',
    'ingest_bp',
    'corpus_bp',
    'integrity_bp',
    'listen_bp'
]
