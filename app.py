import os
from flask import Flask, render_template, jsonify, redirect
from models.db import get_db
# Import modules (optional, for future use)
#from modules.poster import PosterService

# =====================================================
# APP INITIALIZATION
# =====================================================

app = Flask(__name__)

# Load configuration
app.config['SECRET_KEY'] = os.environ.get(
    'SECRET_KEY',
    'your-secret-key-here-change-in-production'
)

app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024

# =====================================================
# IMPORT BLUEPRINTS
# =====================================================

from routes import main_bp, poets_bp, ghazals_bp

# =====================================================
# REGISTER BLUEPRINTS
# =====================================================

app.register_blueprint(main_bp)
app.register_blueprint(poets_bp, url_prefix="/poets")
app.register_blueprint(ghazals_bp, url_prefix="/ghazals")


# =====================================================
# GLOBAL REDIRECT ROUTES
# =====================================================

@app.route("/ghazal/<int:text_id>")
def global_ghazal_redirect(text_id):
    """Direct ghazal access - redirects to ghazal page"""
    return redirect(f"/ghazals/ghazal/{text_id}")


@app.route("/poster/<int:text_id>")
def global_poster_redirect(text_id):
    """Direct poster access"""
    return redirect(f"/ghazals/poster/{text_id}")


@app.route("/view/<int:text_id>")
def global_view_redirect(text_id):
    """Old compatibility route - redirects to poster page"""
    return redirect(f"/ghazals/poster/{text_id}")


# =====================================================
# HEALTH CHECK
# =====================================================

@app.route("/health")
def health():
    return jsonify({
        "status": "ok",
        "project": "UCPC Poetry Archive",
        "message": "Server is running",
        "version": "2.0"
    })


# =====================================================
# DEBUG DATABASE CONNECTION
# =====================================================

@app.route("/debug-db")
def debug_db():
    """Check database connection (remove in production)"""
    try:
        conn = get_db()
        cur = conn.cursor()

        cur.execute("SELECT current_database()")
        db_name = cur.fetchone()

        cur.execute("SELECT COUNT(*) as count FROM poets")
        poet_count = cur.fetchone()

        cur.execute("SELECT COUNT(*) as count FROM texts")
        ghazal_count = cur.fetchone()

        cur.execute("SELECT COALESCE(SUM(views), 0) as total FROM texts")
        total_views = cur.fetchone()

        cur.close()
        conn.close()

        return jsonify({
            "database": db_name[0] if db_name else "unknown",
            "poet_count": poet_count['count'] if poet_count else 0,
            "ghazal_count": ghazal_count['count'] if ghazal_count else 0,
            "total_readers": total_views['total'] if total_views else 0,
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
# RUN APP
# =====================================================

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(
        host="0.0.0.0",
        port=port,
        debug=False
    )
