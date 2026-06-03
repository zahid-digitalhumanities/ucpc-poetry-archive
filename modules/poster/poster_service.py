from .poster_model import PosterModel

class PosterService:
    """Business logic for poster generation"""

    # Available themes with their display names
    THEMES = {
        'black': 'Classic Black',
        'maroon': 'Deep Maroon',
        'blue': 'Night Blue',
        'green': 'Elegant Green',
        'purple': 'Royal Purple'
    }

    @staticmethod
    def build_poster_data(text_id, couplet_limit=4):
        """
        Assembles all data needed to render the poster.
        Returns a dictionary ready to be passed to the template.
        """
        # Increment view count
        PosterModel.increment_views(text_id)

        # Fetch ghazal metadata
        ghazal = PosterModel.get_ghazal_data(text_id)
        if not ghazal:
            return None

        # Fetch verses (limited)
        verses = PosterModel.get_verses(text_id, limit=couplet_limit)

        return {
            'ghazal': ghazal,
            'poster_verses': verses,
            'available_themes': PosterService.THEMES
        }

    @staticmethod
    def get_theme_css_class(theme_name):
        """Return the CSS class for a given theme."""
        if theme_name in PosterService.THEMES:
            return f"theme-{theme_name}"
        return "theme-black"

    @staticmethod
    def get_theme_list():
        """Return list of theme keys for dropdown."""
        return list(PosterService.THEMES.keys())
