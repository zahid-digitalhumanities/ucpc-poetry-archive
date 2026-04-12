from flask import Flask, redirect, url_for, render_template, request, jsonify, abort, send_from_directory, send_file, make_response
from modules.image_generator import generate_ghazal_card
import os
import base64
import time
import uuid
import hashlib
import io
import re

# Blueprints
from routes.main_routes import main_bp
from routes.poets_routes import poets_bp
from routes.ghazals_routes import ghazals_bp
from routes.search_routes import search_bp
from routes.bulk_routes import bulk_bp
from routes.listen_routes import listen_bp

# Models
from models.stats_model import get_stats
from models.ghazal_model import get_ghazal_with_verses

# ==================== CONFIG ====================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
GENERATED_FOLDER = os.path.join(BASE_DIR, 'static', 'generated')
os.makedirs(GENERATED_FOLDER, exist_ok=True)

# ==================== DATABASE ====================
def get_db_connection():
    import psycopg2
    return psycopg2.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        database=os.getenv('DB_NAME', 'ucpc_v3_db'),
        user=os.getenv('DB_USER', 'postgres'),
        password=os.getenv('DB_PASSWORD', '')
    )

# ==================== APP FACTORY ====================
def create_app():
    app = Flask(__name__)
    app.secret_key = os.getenv('SECRET_KEY', 'dev-secret-key')
    app.config['GENERATED_FOLDER'] = GENERATED_FOLDER

    # Register Blueprints
    app.register_blueprint(main_bp)
    app.register_blueprint(poets_bp)
    app.register_blueprint(ghazals_bp)
    app.register_blueprint(search_bp)
    app.register_blueprint(bulk_bp)
    app.register_blueprint(listen_bp)
    print("✅ Blueprints registered")

    # ---------- AFTER REQUEST (allow Facebook bot) ----------
    @app.after_request
    def allow_facebook_bot(response):
        response.headers['Access-Control-Allow-Origin'] = '*'
        return response

    # ---------- Redirects ----------
    @app.route('/admin/add_ghazal')
    def redirect_add_ghazal():
        return redirect(url_for('ghazals.add_ghazal'))

    @app.route('/view/<int:text_id>')
    def redirect_view(text_id):
        return redirect(url_for('ghazals.view_ghazal', text_id=text_id))

    # ---------- Debug ----------
    @app.route('/check')
    def check():
        return "OK WORKING"

    @app.route('/routes')
    def show_routes():
        return "<br>".join([str(rule) for rule in app.url_map.iter_rules()])

    # ---------- Client-side canvas upload ----------
    @app.route('/upload_image', methods=['POST'])
    def upload_image():
        data = request.json.get('image')
        if not data:
            return jsonify({'error': 'No image data'}), 400
        header, encoded = data.split(',', 1)
        binary = base64.b64decode(encoded)

        filename = f"share_{uuid.uuid4().hex}.png"
        filepath = os.path.join(GENERATED_FOLDER, filename)
        with open(filepath, 'wb') as f:
            f.write(binary)

        full_url = url_for('static', filename=f'generated/{filename}', _external=True)
        return jsonify({'url': full_url})

    # ---------- Generate share image (with dedication) ----------
    @app.route('/generate_share/<int:text_id>')
    def generate_share(text_id):
        try:
            dedicator = request.args.get('dedicator', '')
            dedicatee = request.args.get('dedicatee', '')

            result = get_ghazal_with_verses(text_id)
            if not result:
                return jsonify({'error': 'Ghazal not found'}), 404

            if isinstance(result, tuple):
                ghazal, verses = result
            else:
                ghazal = result.get('ghazal')
                verses = result.get('verses')

            # Debug
            print(f"Verses count: {len(verses)}")
            if verses:
                print(f"First verse keys: {verses[0].keys()}")

            img = generate_ghazal_card(ghazal, verses, dedicator, dedicatee)

            filename = f"share_{uuid.uuid4().hex}.png"
            filepath = os.path.join(GENERATED_FOLDER, filename)
            img.save(filepath)

            # Remove .png from URL for Facebook (HTML page)
            name_without_ext = filename.replace('.png', '')
            share_url = url_for('share_page', filename=name_without_ext, _external=True)
            return jsonify({'share_url': share_url})

        except Exception as e:
            import traceback
            traceback.print_exc()
            return jsonify({'error': str(e)}), 500

    # ---------- Share page (HTML with OG tags) – no .png in URL ----------
    @app.route('/share_page/<filename>')
    def share_page(filename):
        if not filename.endswith('.png'):
            filename_png = filename + '.png'
        else:
            filename_png = filename
        image_url = url_for('static', filename=f'generated/{filename_png}', _external=True)
        return render_template('share.html', image_url=image_url)

    # ---------- Direct OG image (no file save) ----------
    @app.route('/og-image/<int:text_id>')
    def og_image(text_id):
        result = get_ghazal_with_verses(text_id)
        if not result:
            abort(404)
        if isinstance(result, tuple):
            ghazal, verses = result
        else:
            ghazal = result.get('ghazal')
            verses = result.get('verses')
        if not ghazal:
            abort(404)
        img = generate_ghazal_card(ghazal, verses, '', '')
        buf = io.BytesIO()
        img.save(buf, format='PNG')
        buf.seek(0)
        return send_file(buf, mimetype='image/png')

    # ---------- robots.txt (allow Facebook crawler) ----------
    @app.route('/robots.txt')
    def robots():
        return send_from_directory('static', 'robots.txt')

    # ---------- 🔥 NEW: TEXT SHARE (full ghazal as text) ----------
    @app.route('/share_text/<int:text_id>')
    def share_text(text_id):
        dedicator = request.args.get('dedicator', '')
        dedicatee = request.args.get('dedicatee', '')

        result = get_ghazal_with_verses(text_id)
        if not result:
            return "Ghazal not found", 404

        if isinstance(result, tuple):
            ghazal, verses = result
        else:
            ghazal = result.get('ghazal')
            verses = result.get('verses')

        text = ""

        # Poet name (uppercase)
        text += f"{ghazal.get('poet_name', '').upper()}\n\n"

        # Full ghazal verses
        for v in verses:
            m1 = v.get('misra1_urdu', '')
            m2 = v.get('misra2_urdu', '')
            text += f"{m1}\n{m2}\n\n"

        # Dedication
        if dedicator:
            text += f"From: {dedicator}\n"
        if dedicatee:
            text += f"To: {dedicatee}\n"

        text += "\n📖 UCPC Poetry Archive"

        return text

    # ---------- Global stats ----------
    @app.context_processor
    def inject_stats():
        try:
            return dict(stats=get_stats())
        except Exception as e:
            print("⚠️ Stats error:", str(e))
            return dict(stats=None)

    # ---------- Error handlers ----------
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('404.html'), 404

    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template('500.html'), 500

    return app

app = create_app()

if __name__ == '__main__':
    port = int(os.getenv('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False)