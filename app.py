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

    print("🔥 APP FILE LOADED")

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

    # 🔍 Route Debug
    @app.route('/routes')
    def show_routes():
        return "<br>".join([str(rule) for rule in app.url_map.iter_rules()])

    # =========================================================
    # 📤 IMAGE UPLOAD (SOCIAL SHARING)
    # =========================================================
    @app.route('/upload_image', methods=['POST'])
    def upload_image():
        data = request.json.get('image')
        if not data:
            return jsonify({'error': 'No image data'}), 400

        try:
            header, encoded = data.split(',', 1)
            binary = base64.b64decode(encoded)

            generated_dir = os.path.join(os.path.dirname(__file__), 'static', 'generated')
            os.makedirs(generated_dir, exist_ok=True)

            filename = f"{int(time.time())}.png"
            filepath = os.path.join(generated_dir, filename)

            with open(filepath, 'wb') as f:
                f.write(binary)

            base_url = request.host_url.rstrip('/')

            image_url = f"{base_url}/static/generated/{filename}"
            share_url = f"{base_url}/share/{filename}"

            return jsonify({
                "image_url": image_url,
                "share_url": share_url
            })

        except Exception as e:
            print("❌ Upload Error:", str(e))
            return jsonify({"error": "Upload failed"}), 500

    # =========================================================
    # 🌐 SHARE PAGE (ALL SOCIAL PLATFORMS)
    # =========================================================
    @app.route('/share/<filename>')
    def share_image_page(filename):
        """
        Universal share page:
        Works on WhatsApp, Facebook, LinkedIn, X
        """

        base_url = request.host_url.rstrip('/')
        image_url = f"{base_url}/static/generated/{filename}"
        page_url = f"{base_url}/share/{filename}"

        # 🔥 Dynamic content (future: DB se load kar sakte ho)
        title = request.args.get('title', 'UCPC Poetry Archive')
        description = request.args.get('desc', 'Beautiful Urdu & English Ghazal')

        return render_template(
            'share.html',
            image_url=image_url,
            title=title,
            description=description,
            page_url=page_url
        )

    # =========================================================
    # 📊 GLOBAL STATS
    # =========================================================
    @app.context_processor
    def inject_stats():
        try:
            return dict(stats=get_stats())
        except Exception as e:
            print("⚠️ Stats error:", str(e))
            return dict(stats=None)

    # =========================================================
    # ❌ ERROR HANDLERS
    # =========================================================
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('404.html'), 404

    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template('500.html'), 500

    return app


# =========================================================
# 🚀 CREATE APP
# =========================================================
app = create_app()

# =========================================================
# 🚀 RUN (RENDER COMPATIBLE)
# =========================================================
if __name__ == "__main__":
    # Get port from environment (Render sets PORT, default 10000)
    port = int(os.environ.get("PORT", 10000))
    
    # Determine if we are in production (e.g., Render) or local
    # Production should never use debug=True
    debug_mode = os.environ.get("FLASK_ENV") != "production" and not os.environ.get("RENDER")
    
    print(f"🔥 Running on port {port} (debug={debug_mode})")
    app.run(host="0.0.0.0", port=port, debug=debug_mode)
