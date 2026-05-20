import os
from flask import Flask, render_template, jsonify

# =====================================================
# APP INITIALIZATION
# =====================================================

app = Flask(__name__)

# Load configuration
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-here-change-in-production')
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB max upload

# =====================================================
# IMPORT AND REGISTER BLUEPRINTS
# =====================================================

from routes.main_routes import main_bp
from routes.poets_routes import poets_bp
from routes.ghazals_routes import ghazals_bp

app.register_blueprint(main_bp)
app.register_blueprint(poets_bp, url_prefix="/poets")
app.register_blueprint(ghazals_bp, url_prefix="/ghazals")

# =====================================================
# HEALTH CHECK (for Render)
# =====================================================

@app.route("/health")
def health():
    return jsonify({
        "status": "ok",
        "project": "UCPC Poetry Archive",
        "message": "Server is running"
    })

# =====================================================
# DEBUG DATABASE CONNECTION (Remove after testing)
# =====================================================

@app.route("/debug-db")
def debug_db():
    """Temporary route to check database connection"""
    try:
        from models.db import get_db
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT current_database()")
        db_name = cur.fetchone()
        cur.execute("SELECT COUNT(*) FROM poets")
        poet_count = cur.fetchone()
        cur.close()
        conn.close()
        return jsonify({
            "database": db_name[0] if db_name else "unknown",
            "poet_count": poet_count[0] if poet_count else 0,
            "status": "connected"
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

# =====================================================
# ERROR HANDLERS
# =====================================================

@app.errorhandler(404)
def not_found(e):
    return render_template("404.html"), 404

@app.errorhandler(500)
def server_error(e):
    return render_template("500.html"), 500

# =====================================================
# RUN (for local development only)
# =====================================================

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
