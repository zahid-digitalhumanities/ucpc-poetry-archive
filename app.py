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
from routes.listen_routes import listen_bp
from routes.similarity_route import similarity_bp
from routes.insights_routes import insights_bp
from routes.ingest_routes import ingest_bp
from routes.ai_routes import ai_bp
from routes.ask_ucpc_route import ask_bp
from routes.ask_ucpc_index import ask_ucpc_bp as ask_index_bp  # Fixed: import with alias
from routes.research_dashboard import research_dashboard_bp
from routes.corpus_routes import corpus_bp          
from routes.dh_advanced import dh_bp
from routes.integrity_routes import integrity_bp
from routes.semantic_routes import semantic_bp
from routes.research_validation_routes import validation_bp

# ==================== CONFIG ====================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
GENERATED_FOLDER = os.path.join(BASE_DIR, 'static', 'generated')
os.makedirs(GENERATED_FOLDER, exist_ok=True)

# ==================== DATABASE ====================
def get_db_connection():
    import psycopg2
    from psycopg2.extras import RealDictCursor
    return psycopg2.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        database=os.getenv('DB_NAME', 'ucpc_v3_db'),
        user=os.getenv('DB_USER', 'postgres'),
        password=os.getenv('DB_PASSWORD', ''),
        cursor_factory=RealDictCursor
    )

# ==================== APP FACTORY ====================
def create_app():
    app = Flask(__name__)
    app.secret_key = os.getenv('SECRET_KEY', 'dev-secret-key')
    app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024   # 50 MB
    app.config['GENERATED_FOLDER'] = GENERATED_FOLDER

    # Register Blueprints
    app.register_blueprint(main_bp)
    app.register_blueprint(poets_bp)
    app.register_blueprint(ghazals_bp)
    app.register_blueprint(search_bp)
    app.register_blueprint(listen_bp)
    app.register_blueprint(similarity_bp)
    app.register_blueprint(insights_bp)
    app.register_blueprint(ingest_bp)
    app.register_blueprint(ai_bp)
    app.register_blueprint(ask_bp)
    app.register_blueprint(ask_index_bp)  # Now works because of alias
    app.register_blueprint(corpus_bp)
    app.register_blueprint(research_dashboard_bp)
    app.register_blueprint(dh_bp)
    app.register_blueprint(integrity_bp)
    app.register_blueprint(semantic_bp)
    app.register_blueprint(validation_bp)
    
    print("✅ Blueprints registered")
    print("   - Research Dashboard: /research")
    print("   - Ask UCPC Index: /ask-index")
    print("   - AI Routes: /api/ai")
    print("   - Integrity Dashboard: /integrity")

    # ---------- AFTER REQUEST ----------
    @app.after_request
    def add_security_headers(response):
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['ngrok-skip-browser-warning'] = 'true'
        return response

    # ---------- Redirects ----------
    @app.route('/admin/add_ghazal')
    def redirect_add_ghazal():
        return redirect(url_for('ingest.add'))

    @app.route('/view/<int:text_id>')
    def redirect_view(text_id):
        return redirect(url_for('ghazals.view_ghazal', text_id=text_id))

    # ---------- Debug ----------
    @app.route('/check')
    def check():
        return "OK WORKING"

    @app.route('/routes')
    def show_routes():
        routes = []
        for rule in app.url_map.iter_rules():
            routes.append(f"{rule.endpoint}: {rule}")
        return "<br>".join(sorted(routes))

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

    # ---------- Share page (HTML with OG tags) ----------
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

    # ---------- Global stats ----------
    @app.context_processor
    def inject_stats():
        try:
            from models.stats_model import get_stats
            return dict(stats=get_stats())
        except Exception as e:
            print("⚠️ Stats error:", str(e))
            return dict(stats=None)

    # ---------- Template filter for enumerate ----------
    @app.template_filter('enumerate')
    def jinja_enumerate(iterable, start=1):
        return enumerate(iterable, start)

    # ---------- Random Ghazal API ----------
    @app.route('/api/random-ghazal')
    def random_ghazal():
        from models.base import get_db_connection
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT id FROM texts WHERE form = 'ghazal' AND (is_deleted = FALSE OR is_deleted IS NULL) ORDER BY RANDOM() LIMIT 1")
        row = cur.fetchone()
        cur.close()
        conn.close()
        if row:
            return jsonify({'id': row['id']})
        return jsonify({'error': 'No ghazals found'}), 404

    # ---------- Research Dashboard Redirect ----------
    @app.route('/research-dashboard')
    def research_dashboard_redirect():
        return redirect(url_for('research_dashboard.dashboard'))

    # ---------- API Documentation ----------
    @app.route('/api/docs')
    def api_docs():
        return jsonify({
            "name": "UCPC Poetry Archive API",
            "version": "2.0",
            "endpoints": {
                "research": {
                    "analyze": "/research/api/analyze (POST)",
                    "health": "/research/api/health (GET)",
                    "model_info": "/research/api/model-info (GET)",
                    "corpus_stats": "/research/api/corpus-stats (GET)",
                    "batch": "/research/api/batch (POST)"
                },
                "poet_prediction": {
                    "predict": "/api/ai/predict-poet (POST)",
                    "by_id": "/api/ai/predict-poet/<text_id> (GET)"
                },
                "search": {
                    "search": "/search/ (GET)",
                    "suggest": "/search/suggest (GET)"
                },
                "integrity": {
                    "dashboard": "/integrity/ (GET)",
                    "stats": "/integrity/api/stats (GET)"
                }
            },
            "documentation": "https://github.com/ucpc/poetry-archive"
        })

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