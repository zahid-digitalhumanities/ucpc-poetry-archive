from .main_routes import main_bp
from .poets_routes import poets_bp
from .ghazals_routes import ghazals_bp
from .search_routes import search_bp
from .poet_redirect import poet_redirect_bp

__all__ = ['main_bp', 'poets_bp', 'ghazals_bp', 'search_bp', 'poet_redirect_bp']
