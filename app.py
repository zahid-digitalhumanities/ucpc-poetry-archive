# ==================== EMERGENCY STARTUP PATCH - MUST BE FIRST ====================
import startup  # This MUST be the first import - disables heavy models and limits threads
# ==============================================================================

from flask import Flask, redirect, url_for, render_template, request, jsonify, abort, send_from_directory, send_file
from modules.image_generator import generate_ghazal_card
import os
import base64
import uuid
import io
import signal
import sys
import resource
from datetime import datetime

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
from routes.ask_ucpc_index import ask_ucpc_bp as ask_index_bp
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

# ==================== GRACEFUL SHUTDOWN ====================
def signal_handler(sig, frame):
    print(f"📡 Received signal {sig}, shutting down gracefully...")
    sys.exit(0)

signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)

# ==================== MEMORY LIMIT (Render Free Tier) ====================
try:
    # Set soft memory limit to 350MB (leaving room for overhead)
    resource.setrlimit(resource.RLIMIT_AS, (350 * 1024 * 1024, 450 * 1024 * 1024))
    print("✅ Memory limit set to 350MB")
except Exception as e:
    print(f"⚠️ Could not set memory limit: {e}")

# ==================== DATABASE (FIXED FOR RENDER) ====================
def get_db_connection():
    """Get database connection using Render's DATABASE_URL"""
    import psycopg2
    from psycopg2.extras import RealDictCursor
    import os
    
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

# ==================== LAZY LOADING FOR HEAVY MODELS (DISABLED FOR EMERGENCY) ====================
_semantic_engine = None
_poet_predictor = None
_heavy_models_loaded = False

def load_heavy_models():
    """Lazy load heavy AI models - ALL DISABLED for emergency fix"""
    global _semantic_engine, _poet_predictor, _heavy_models_loaded
    
    if _heavy_models_loaded:
        return True
    
    # FORCE DISABLE all heavy models - emergency fix
    print("⚠️ Heavy models are DISABLED for emergency stability")
    print("   To enable: Remove DISABLE_HEAVY_MODELS env var and restart")
    _semantic_engine = None
    _poet_predictor = None
    _heavy_models_loaded = True
    return True

# ==================== APP FACTORY ====================
def create_app():
    app = Flask(__name__)
    app.secret_key = os.getenv('SECRET_KEY', 'ucpc-production-secret-key-change-this')
    app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50 MB
    app.config['GENERATED_FOLDER'] = GENERATED_FOLDER
    app.config['JSON_AS_ASCII'] = False  # Support Urdu text
    
    # Register Blueprints
    blueprints = [
        (main_bp, '/'),
        (poets_bp, '/poets'),
        (ghazals_bp, '/ghazals'),
        (search_bp, '/search'),
        (listen_bp, '/listen'),
        (similarity_bp, '/similarity'),
        (insights_bp, '/insights'),
        (ingest_bp, '/ingest'),
        (ai_bp, '/api/ai'),
        (ask_bp, '/ask'),
        (ask_index_bp, '/ask-index'),
        (corpus_bp, '/corpus'),
        (research_dashboard_bp, '/research'),
        (dh_bp, '/dh'),
        (integrity_bp, '/integrity'),
        (semantic_bp, '/semantic'),
        (validation_bp, '/research/validation')
    ]
    
    for blueprint, prefix in blueprints:
        try:
            app.register_blueprint(blueprint)
            print(f"✅ Registered: {prefix}")
        except Exception as e:
            print(f"❌ Failed to register {prefix}: {e}")
    
    print("\n🚀 UCPC Poetry Archive v3.0 - EMERGENCY STABLE MODE")
    print(f"📊 Environment: {'Production' if os.getenv('RENDER') else 'Development'}")
    print(f"💾 Database: {'Configured' if os.getenv('DATABASE_URL') else 'Missing!'}")
    print(f"🧠 Heavy models: FORCE DISABLED (memory safe)")
    print(f"🔧 Render free tier optimized\n")
    
    # ========== HEALTH CHECK ENDPOINT (CRITICAL FOR RENDER) ==========
    @app.route('/health')
    def health_check():
        # Simple health check - no heavy operations
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
            "version": "3.0-emergency",
            "database": db_status,
            "memory_safe": True,
            "heavy_models": "disabled"
        })
    
    # ========== SIMPLE ROOT ROUTE ==========
    @app.route('/')
    def home():
        return "UCPC Poetry Archive is running. Visit /health for status."
    
    # ========== MEMORY DEBUG ENDPOINT ==========
    @app.route('/debug/memory')
    def debug_memory():
        try:
            import psutil
            process = psutil.Process()
            memory_info = process.memory_info()
            return jsonify({
                'rss_mb': round(memory_info.rss / 1024 / 1024, 2),
                'vms_mb': round(memory_info.vms / 1024 / 1024, 2),
                'cpu_percent': process.cpu_percent(),
                'heavy_models_loaded': False
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    # ========== AFTER REQUEST ==========
    @app.after_request
    def add_security_headers(response):
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['ngrok-skip-browser-warning'] = 'true'
        response.headers['X-Content-Type-Options'] = 'nosniff'
        return response
    
    # ========== Redirects ==========
    @app.route('/admin/add_ghazal')
    def redirect_add_ghazal():
        return redirect(url_for('ingest.add'))
    
    @app.route('/view/<int:text_id>')
    def redirect_view(text_id):
        return redirect(url_for('ghazals.view_ghazal', text_id=text_id))
    
    # ========== Debug Routes ==========
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
    
    # ========== Client-side canvas upload ==========
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
    
    # ========== Generate share image ==========
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
    
    # ========== Share page ==========
    @app.route('/share_page/<filename>')
    def share_page(filename):
        if not filename.endswith('.png'):
            filename_png = filename + '.png'
        else:
            filename_png = filename
        image_url = url_for('static', filename=f'generated/{filename_png}', _external=True)
        return render_template('share.html', image_url=image_url)
    
    # ========== OG image ==========
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
    
    # ========== robots.txt ==========
    @app.route('/robots.txt')
    def robots():
        return send_from_directory('static', 'robots.txt')
    
    # ========== Text share ==========
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
    
    # ========== Global stats ==========
    @app.context_processor
    def inject_stats():
        try:
            from models.stats_model import get_stats
            return dict(stats=get_stats())
        except Exception as e:
            print(f"⚠️ Stats error: {e}")
            return dict(stats=None)
    
    # ========== Template filter ==========
    @app.template_filter('enumerate')
    def jinja_enumerate(iterable, start=1):
        return enumerate(iterable, start)
    
    # ========== Random Ghazal API ==========
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
    
    # ========== Research Dashboard Redirect ==========
    @app.route('/research-dashboard')
    def research_dashboard_redirect():
        return redirect(url_for('research_dashboard.dashboard'))
    
    # ========== API Documentation ==========
    @app.route('/api/docs')
    def api_docs():
        return jsonify({
            "name": "UCPC Poetry Archive API",
            "version": "3.0-emergency",
            "environment": "production" if os.getenv('RENDER') else "development",
            "status": "stable (heavy models disabled)",
            "endpoints": {
                "health": "/health (GET)",
                "check": "/check (GET)",
                "debug_memory": "/debug/memory (GET)"
            }
        })
    
    # ========== Error Handlers ==========
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('404.html'), 404
    
    @app.errorhandler(500)
    def internal_server_error(e):
        return jsonify({
            "error": "Internal server error",
            "message": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500
    
    @app.errorhandler(413)
    def too_large(e):
        return jsonify({"error": "File too large", "max_size_mb": 50}), 413
    
    return app


# ==================== CREATE APP INSTANCE ====================
app = create_app()

# ==================== RUN (Local Development Only) ====================
if __name__ == '__main__':
    port = int(os.getenv('PORT', 10000))
    print(f"🔥 Starting UCPC in development mode on port {port}")
    app.run(host='0.0.0.0', port=port, debug=True, threaded=True)
