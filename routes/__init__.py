# routes/__init__.py
from .main_routes import main_bp
from .poets_routes import poets_bp
from .ghazals_routes import ghazals_bp
from .search_routes import search_bp

# Optional – only if files exist
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
