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

    # 🔐 Secret Key
    app.secret_key = os.getenv('SECRET_KEY', 'dev-secret-key')

    # ✅ Register Blueprints
    app.register_blueprint(main_bp)
    app.register_blueprint(poets_bp)
    app.register_blueprint(ghazals_bp)
    app.register_blueprint(search_bp)
    app.register_blueprint(bulk_bp)
    app.register_blueprint(listen_bp)

    print("🔥 Blueprints registered successfully")

    # 🔁 Redirect routes
    @app.route('/admin/add_ghazal')
    def redirect_add_ghazal():
        return redirect(url_for('ghazals.add_ghazal'))

    @app.route('/view/<int:text_id>')
    def redirect_view(text_id):
        return redirect(url_for('ghazals.view_ghazal', text_id=text_id))

    # 🧪 Debug route
    @app.route('/check')
    def check():
        return "OK WORKING"

    # 🔥 ROUTE DEBUG (VERY IMPORTANT)
    @app.route('/routes')
    def show_routes():
        return "<br>".join([str(rule) for rule in app.url_map.iter_rules()])

    # 📤 Image upload route (for social sharing)
    @app.route('/upload_image', methods=['POST'])
    def upload_image():
        data = request.json.get('image')
        if not data:
            return jsonify({'error': 'No image data'}), 400

        # Extract base64 data
        header, encoded = data.split(',', 1)
        binary = base64.b64decode(encoded)

        # Ensure generated folder exists
        generated_dir = os.path.join(os.path.dirname(__file__), 'static', 'generated')
        os.makedirs(generated_dir, exist_ok=True)

        # Generate unique filename
        filename = f"{int(time.time())}.png"
        filepath = os.path.join(generated_dir, filename)

        with open(filepath, 'wb') as f:
            f.write(binary)

        # Return the full public URL
        full_url = request.host_url + f"static/generated/{filename}"
        return jsonify({'url': full_url})

    # 📤 Share page route (for rich social previews)
    @app.route('/share/<filename>')
    def share_image_page(filename):
        """Serve a share page with OG meta tags pointing to the image."""
        image_url = request.host_url + f"static/generated/{filename}"
        return render_template('share.html', image_url=image_url)

    # 📊 Global stats
    @app.context_processor
    def inject_stats():
        try:
            return dict(stats=get_stats())
        except Exception as e:
            print("⚠️ Stats error:", str(e))
            return dict(stats=None)

    # ❌ 404
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('404.html'), 404

    # ❌ 500
    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template('500.html'), 500

    return app


# 🚀 Create App
app = create_app()

# ✅ IMPORTANT FOR RENDER
import os

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    print(f"🔥 Running on port {port}")
    app.run(host="0.0.0.0", port=port)