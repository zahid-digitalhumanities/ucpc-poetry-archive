from flask import Flask, redirect, url_for, render_template, request, jsonify
import os
import base64
import time

# Blueprints
from routes.main_routes import main_bp
from routes.poets_routes import poets_bp
from routes.ghazals_routes import ghazals_bp
from routes.search_routes import search_bp
from routes.bulk_routes import bulk_bp
from routes.listen_routes import listen_bp

# Models
from models.stats_model import get_stats

def create_app():
    app = Flask(__name__)
    app.secret_key = os.getenv('SECRET_KEY', 'dev-secret-key')

    # Register blueprints
    app.register_blueprint(main_bp)
    app.register_blueprint(poets_bp)
    app.register_blueprint(ghazals_bp)
    app.register_blueprint(search_bp)
    app.register_blueprint(bulk_bp)
    app.register_blueprint(listen_bp)

    # Redirects
    @app.route('/admin/add_ghazal')
    def redirect_add_ghazal():
        return redirect(url_for('ghazals.add_ghazal'))

    @app.route('/view/<int:text_id>')
    def redirect_view(text_id):
        return redirect(url_for('ghazals.view_ghazal', text_id=text_id))

    # Share page (for social previews)
    @app.route('/share/<filename>')
    def share_page(filename):
        image_url = request.host_url + f"static/generated/{filename}"
        return render_template('share.html', image_url=image_url)

    # Global stats
    @app.context_processor
    def inject_stats():
        try:
            return dict(stats=get_stats())
        except Exception as e:
            print("⚠️ Stats error:", str(e))
            return dict(stats=None)

    # Error handlers
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('404.html'), 404

    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template('500.html'), 500

    return app

app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, debug=False)