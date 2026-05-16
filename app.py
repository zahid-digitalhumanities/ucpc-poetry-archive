# ==================== EMERGENCY STARTUP - MUST BE FIRST ====================
import startup  # MUST BE FIRST LINE - disables heavy models
# ==========================================================================

from flask import Flask, redirect, url_for, render_template, request, jsonify, abort, send_from_directory, send_file, make_response
from modules.image_generator import generate_ghazal_card
import os
import base64
import time
import uuid
import hashlib
import io
import re
import sys

# ==================== SAFE BLUEPRINT IMPORTS ====================
# Only import blueprints that work on free tier
from routes.main_routes import main_bp
from routes.poets_routes import poets_bp
from routes.ghazals_routes import ghazals_bp
from routes.search_routes import search_bp

# DISABLED for free tier (heavy or problematic):
# from routes.bulk_routes import bulk_bp           # DISABLED - may have heavy NLP
# from routes.listen_routes import listen_bp       # DISABLED - audio processing
from routes.similarity_route import similarity_bp   # KEEP - we fixed this
# from routes.fingerprint import fingerprint_bp     # DISABLED - unknown
# from routes.insights_routes import insights_bp   # DISABLED - may have ML
# from routes.poet_prediction import poet_bp       # DISABLED - use lite predictor instead

# ==================== CONFIG ====================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
GENERATED_FOLDER = os.path.join(BASE_DIR, 'static', 'generated')
os.makedirs(GENERATED_FOLDER, exist_ok=True)

# ==================== DATABASE (FIXED FOR RENDER) ====================
def get_db_connection():
    """Get database connection using Render's DATABASE_URL with SSL."""
    import psycopg2
    from psycopg2.extras import RealDictCursor
    
    database_url = os.getenv('DATABASE_URL')
    
    if database_url:
        # Ensure SSL mode is required for Render
        if 'sslmode' not in database_url:
            if '?' in database_url:
                database_url += '&sslmode=require'
            else:
                database_url += '?sslmode=require'
        return psycopg2.connect(database_url, cursor_factory=RealDictCursor)
    else:
        # Fallback for local development
        return psycopg2.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            database=os.getenv('DB_NAME', 'ucpc_v3_db'),
            user=os.getenv('DB_USER', 'postgres'),
            password=os.getenv('DB_PASSWORD', ''),
            port=os.getenv('DB_PORT', '5432'),
            cursor_factory=RealDictCursor
        )

# ==================== APP FACTORY ====================
def create_app():
    app = Flask(__name__)
    app.secret_key = os.getenv('SECRET_KEY', 'ucpc-free-tier-secret-key')
    app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024   # 50 MB
    app.config['GENERATED_FOLDER'] = GENERATED_FOLDER
    app.config['JSON_AS_ASCII'] = False  # Support Urdu text

    # Register Blueprints (only safe ones)
    app.register_blueprint(main_bp)
    app.register_blueprint(poets_bp)
    app.register_blueprint(ghazals_bp)
    app.register_blueprint(search_bp)
    # app.register_blueprint(bulk_bp)        # DISABLED
    # app.register_blueprint(listen_bp)      # DISABLED
    app.register_blueprint(similarity_bp)     # KEPT - fixed version
    # app.register_blueprint(fingerprint_bp)  # DISABLED
    # app.register_blueprint(insights_bp)    # DISABLED
    # app.register_blueprint(poet_bp)        # DISABLED - use /ask-index instead

    print("✅ Blueprints registered (free tier optimized)")
    print("   - / (main)")
    print("   - /poets")
    print("   - /ghazals")
    print("   - /search")
    print("   - /similarity")

    # ========== HEALTH CHECK ENDPOINT (CRITICAL FOR RENDER) ==========
    @app.route('/health')
    def health_check():
        db_status = "unknown"
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("SELECT 1")
            cur.close()
            conn.close()
            db_status = "connected"
        except Exception as e:
            db_status = f"error: {str(e)[:50]}"
        
        return jsonify({
            "status": "ok",
            "project": "UCPC Poetry Archive",
            "version": "3.0-free-tier",
            "database": db_status,
            "memory_safe": True,
            "heavy_models": "disabled"
        })

    # ========== SIMPLE ROOT ROUTE ==========
    @app.route('/')
    def home():
        return "UCPC Poetry Archive is running. Visit /health for status."

    # ---------- AFTER REQUEST (allow Facebook bot & skip ngrok warning) ----------
    @app.after_request
    def add_security_headers(response):
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['ngrok-skip-browser-warning'] = 'true'
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
        return "✅ UCPC Poetry Archive is running!"

    @app.route('/routes')
    def show_routes():
        routes = []
        for rule in app.url_map.iter_rules():
            if not rule.endpoint.startswith('static'):
                routes.append(f"{rule.endpoint}: {rule}")
        return "<br>".join(sorted(routes[:50]))

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

            from models.ghazal_model import get_ghazal_with_verses
            result = get_ghazal_with_verses(text_id)
            if not result:
                return jsonify({'error': 'Ghazal not found'}), 404

            if isinstance(result, tuple):
                ghazal, verses = result
            else:
                ghazal = result.get('ghazal')
                verses = result.get('verses')

            img = generate_ghazal_card(ghazal, verses, dedicator, dedicatee)

            filename = f"share_{uuid.uuid4().hex}.png"
            filepath = os.path.join(GENERATED_FOLDER, filename)
            img.save(filepath)

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
        from models.ghazal_model import get_ghazal_with_verses
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

    # ---------- robots.txt ----------
    @app.route('/robots.txt')
    def robots():
        return send_from_directory('static', 'robots.txt')

    # ---------- TEXT SHARE (with dedication) ----------
    @app.route('/share_text/<int:text_id>')
    def share_text(text_id):
        dedicator = request.args.get('dedicator', '')
        dedicatee = request.args.get('dedicatee', '')

        from models.ghazal_model import get_ghazal_with_verses
        result = get_ghazal_with_verses(text_id)
        if not result:
            return "Ghazal not found", 404

        if isinstance(result, tuple):
            ghazal, verses = result
        else:
            ghazal = result.get('ghazal')
            verses = result.get('verses')

        text = ""
        poet = ghazal.get('poet_name', '').upper()
        text += f"{poet}\n"
        text += "-" * len(poet) + "\n\n"

        if dedicator:
            text += f"From: {dedicator}\n"
        if dedicatee:
            text += f"To: {dedicatee}\n"
        text += "\n"

        for v in verses:
            m1 = v.get('misra1_urdu', '')
            m2 = v.get('misra2_urdu', '')
            text += f"{m1}\n{m2}\n\n"

        text += "📖 UCPC Poetry Archive"
        return text

    # ---------- Global stats (safe version) ----------
    @app.context_processor
    def inject_stats():
        try:
            from models.stats_model import get_stats
            return dict(stats=get_stats())
        except Exception as e:
            print(f"⚠️ Stats error: {e}")
            return dict(stats=None)

    # ---------- Template filter for enumerate ----------
    @app.template_filter('enumerate')
    def jinja_enumerate(iterable, start=1):
        return enumerate(iterable, start)

    # ---------- Poet Prediction API (DISABLED - use /ask-index instead) ----------
    @app.route('/api/predict-poet/<int:text_id>')
    def api_predict_poet(text_id):
        return jsonify({
            'success': False,
            'error': 'Poet prediction API disabled on free tier',
            'alternative': 'Use /ask-index/ endpoint'
        }), 503

    # ---------- Random Ghazal API ----------
    @app.route('/api/random-ghazal')
    def random_ghazal():
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("SELECT id FROM texts WHERE form = 'ghazal' AND (is_deleted = FALSE OR is_deleted IS NULL) ORDER BY RANDOM() LIMIT 1")
            row = cur.fetchone()
            cur.close()
            conn.close()
            if row:
                return jsonify({'id': row['id']})
            return jsonify({'error': 'No ghazals found'}), 404
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    # ---------- Error handlers ----------
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('404.html'), 404

    @app.errorhandler(500)
    def internal_server_error(e):
        return jsonify({
            "error": "Internal server error",
            "message": str(e),
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }), 500

    return app


# ==================== CREATE APP INSTANCE ====================
app = create_app()

# ==================== RUN (Local Development Only) ====================
if __name__ == '__main__':
    port = int(os.getenv('PORT', 10000))
    print(f"🔥 Starting UCPC in development mode on port {port}")
    app.run(host='0.0.0.0', port=port, debug=True, threaded=True)
