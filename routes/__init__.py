# This file makes the routes directory a Python package
# Import all blueprints to make them available
from .main_routes import main_bp
from .poets_routes import poets_bp
from .ghazals_routes import ghazals_bp

# List of all blueprints for easy access
__all__ = ['main_bp', 'poets_bp', 'ghazals_bp']