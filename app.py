import os
from flask import Flask, render_template, jsonify, redirect, request
from models.db import get_db

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
    Public global route for direct ghazal access
    Example: /ghazal/1833
    Redirects to full ghazal page
    """
    return redirect(f"/ghazals/ghazal/{text_id}")


@app.route("/ghazal/<int:text_id>/full")
def global_ghazal_full_redirect(text_id):
    """
    Direct full ghazal access
    Example: /ghazal/1833/full
    """
    return redirect(f"/ghazals/ghazal/{text_id}/full")


@app.route("/view/<int:text_id>")
def global_view_redirect(text_id):
    """
    Old compatibility route for poster page
    Example: /view/1833
    """
    return redirect(f"/ghazals/view/{text_id}")


# =====================================================
# VISITOR COUNTER API (Persistent Database Version)
# =====================================================

@app.route("/api/visitor-count")
def api_visitor_count():
    """Get total visitors from database"""
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT COALESCE(SUM(views), 0) as total FROM texts")
        result = cur.fetchone()
        cur.close()
        conn.close()
        return jsonify({
            "visitors": result['total'] if result else 0
        })
    except Exception as e:
        return jsonify({
            "visitors": 0,
            "error": str(e)
        }), 500


# =====================================================
# SITEMAP (For SEO)
# =====================================================

@app.route("/sitemap.xml")
def sitemap():
    """Generate basic sitemap for search engines"""
    base_url = request.host_url.rstrip('/')
    pages = [
        '/',
        '/poets',
        '/health'
    ]
    
    # Add all ghazal IDs to sitemap
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT id FROM texts ORDER BY id DESC LIMIT 500")
        ghazals = cur.fetchall()
        cur.close()
        conn.close()
        
        for ghazal in ghazals:
            pages.append(f'/ghazals/view/{ghazal["id"]}')
            pages.append(f'/ghazals/ghazal/{ghazal["id"]}/full')
    except:
        pass
    
    sitemap_xml = '<?xml version="1.0" encoding="UTF-8"?>\n'
    sitemap_xml += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    
    for page in pages:
        sitemap_xml += '  <url>\n'
        sitemap_xml += f'    <loc>{base_url}{page}</loc>\n'
        sitemap_xml += '    <priority>0.8</priority>\n'
        sitemap_xml += '  </url>\n'
    
    sitemap_xml += '</urlset>'
    
    return sitemap_xml, 200, {'Content-Type': 'application/xml'}


# =====================================================
# ROBOTS.TXT (For Search Engines)
# =====================================================

@app.route("/robots.txt")
def robots_txt():
    """Robots.txt for search engine crawlers"""
    content = """User-agent: *
Allow: /
Disallow: /debug-db
Disallow: /health

Sitemap: https://ucpc-poetry-archive.onrender.com/sitemap.xml
"""
    return content, 200, {'Content-Type': 'text/plain'}


# =====================================================
# GLOBAL CONTEXT PROCESSOR
# =====================================================

@app.context_processor
def utility_processor():
    """Make total_visitors available to all templates"""
    def get_total_visitors():
        try:
            conn = get_db()
            cur = conn.cursor()
            cur.execute("SELECT COALESCE(SUM(views), 0) as total FROM texts")
            result = cur.fetchone()
            cur.close()
            conn.close()
            return result['total'] if result else 0
        except:
            return 0
    
    return dict(total_visitors=get_total_visitors())


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
        from models.db import get_db

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
        debug=False  # Set to False in production
    )