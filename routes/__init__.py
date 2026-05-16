from .main_routes import main_bp
from .poets_routes import poets_bp
from .ghazals_routes import ghazals_bp
# from .search_routes import search_bp   # uncomment when ready
# from .bulk_routes import bulk_bp       # uncomment when ready

all_blueprints = [main_bp, poets_bp, ghazals_bp]