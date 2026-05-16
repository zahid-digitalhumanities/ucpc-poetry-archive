# routes/__init__.py - Free tier optimized
# Only import blueprints that work without heavy ML packages

from .main_routes import main_bp
from .poets_routes import poets_bp
from .ghazals_routes import ghazals_bp
from .search_routes import search_bp

# DISABLED for free tier (require heavy packages like sentence_transformers, torch, etc.):
# from .bulk_routes import bulk_bp           # DISABLED - requires embeddings
# from .listen_routes import listen_bp       # DISABLED - audio processing
from .similarity_route import similarity_bp   # KEPT - lightweight version
# from .fingerprint import fingerprint_bp     # DISABLED - unknown dependencies
# from .insights_routes import insights_bp   # DISABLED - may have ML
# from .poet_prediction import poet_bp       # DISABLED - use lite predictor instead
