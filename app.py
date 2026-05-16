from flask import Flask, redirect, url_for, render_template, request, jsonify
from routes.main_routes import main_bp
from routes.poets_routes import poets_bp
from routes.ghazals_routes import ghazals_bp
from routes.search_routes import search_bp
from routes.bulk_routes import bulk_bp
from models.stats_model import get_stats
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Use environment variable for secret key in production
app.secret_key = os.environ.get('SECRET_KEY', 'your-secret-key-here-change-this-in-production')

# Configuration
app.config.update(
    SESSION_COOKIE_SECURE=os.environ.get('SESSION_COOKIE_SECURE', 'False').lower() == 'true',
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
)

# Register blueprints
app.register_blueprint(main_bp)
app.register_blueprint(poets_bp)
app.register_blueprint(ghazals_bp)
app.register_blueprint(search_bp)
app.register_blueprint(bulk_bp)

# Health check endpoint for Render
@app.route('/health')
def health_check():
    return jsonify({
        'status': 'healthy',
        'message': 'Server is running',
        'endpoint': request.endpoint
    }), 200

# Readiness probe for Render
@app.route('/ready')
def readiness_check():
    try:
        # Check database connection or other critical services here
        stats = get_stats()
        return jsonify({
            'status': 'ready',
            'stats': stats
        }), 200
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        return jsonify({'status': 'not ready', 'error': str(e)}), 503

@app.route('/admin/add_ghazal')
def redirect_add_ghazal():
    return redirect(url_for('ghazals.add_ghazal'))

@app.route('/view/<int:text_id>')
def redirect_view(text_id):
    return redirect(url_for('ghazals.view_ghazal', text_id=text_id))

@app.context_processor
def inject_stats():
    return dict(stats=get_stats())

@app.context_processor
def inject_year():
    return dict(current_year=os.environ.get('CURRENT_YEAR', '2026'))

# Error handlers with request context
@app.errorhandler(404)
def page_not_found(e):
    logger.warning(f"404 error: {request.url} - endpoint: {request.endpoint}")
    return render_template('404.html', request=request), 404

@app.errorhandler(500)
def internal_server_error(e):
    logger.error(f"500 error: {request.url} - {str(e)}")
    return render_template('500.html', request=request), 500

@app.errorhandler(403)
def forbidden(e):
    return render_template('403.html', request=request), 403

@app.errorhandler(405)
def method_not_allowed(e):
    return render_template('405.html', request=request), 405

# Handle large payloads and timeouts
@app.errorhandler(413)
def request_entity_too_large(e):
    return jsonify({'error': 'File too large. Maximum size is 16MB.'}), 413

@app.errorhandler(504)
def gateway_timeout(e):
    return jsonify({'error': 'Request timeout. Please try again.'}), 504

# Before request handler for security
@app.before_request
def before_request():
    # Log all requests in production
    if not app.debug:
        logger.info(f"{request.method} {request.path} - {request.remote_addr}")

# After request handler for headers
@app.after_request
def after_request(response):
    # Add security headers
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    return response

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    app.run(host='0.0.0.0', port=port, debug=debug)
