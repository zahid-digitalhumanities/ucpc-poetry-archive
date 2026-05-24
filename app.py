import os
from flask import Flask, render_template, jsonify, redirect

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

from routes.main_routes import main_bp
from routes.poets_routes import poets_bp
from routes.ghazals_routes import ghazals_bp

# =====================================================
# REGISTER BLUEPRINTS
# =====================================================

app.register_blueprint(main_bp)

# poets routes
app.register_blueprint(
    poets_bp,
    url_prefix="/poets"
)

# ghazals routes
app.register_blueprint(
    ghazals_bp,
    url_prefix="/ghazals"
)

# =====================================================
# GLOBAL REDIRECT ROUTES
# IMPORTANT FOR FACEBOOK REEL LINKS
# =====================================================

@app.route("/ghazal/<int:text_id>")
def global_ghazal_redirect(text_id):
    """
    Public global route
    Example:
    /ghazal/1833
    """
    return redirect(f"/ghazals/ghazal/{text_id}")


@app.route("/view/<int:text_id>")
def global_view_redirect(text_id):
    """
    Old compatibility route
    Example:
    /view/1833
    """
    return redirect(f"/ghazals/view/{text_id}")


# =====================================================
# VISITOR COUNTER API
# =====================================================

VISITOR_COUNT = 0

@app.before_request
def count_visitors():
    global VISITOR_COUNT
    VISITOR_COUNT += 1


@app.route("/visitor-count")
def visitor_count():
    return jsonify({
        "visitors": VISITOR_COUNT
    })


# =====================================================
# HEALTH CHECK
# =====================================================

@app.route("/health")
def health():
    return jsonify({
        "status": "ok",
        "project": "UCPC Poetry Archive",
        "message": "Server is running"
    })


# =====================================================
# DEBUG DATABASE CONNECTION
# =====================================================

@app.route("/debug-db")
def debug_db():

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
# RUN APP
# =====================================================

if __name__ == "__main__":

    port = int(os.environ.get("PORT", 5000))

    app.run(
        host="0.0.0.0",
        port=port,
        debug=True
    )