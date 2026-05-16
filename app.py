from flask import Flask, redirect, url_for, render_template
from flask import Flask, redirect, url_for
from routes.main_routes import main_bp
from routes.poets_routes import poets_bp
from routes.ghazals_routes import ghazals_bp
from routes.search_routes import search_bp
from routes.bulk_routes import bulk_bp
from models.stats_model import get_stats

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'

app.register_blueprint(main_bp)
app.register_blueprint(poets_bp)
app.register_blueprint(ghazals_bp)
app.register_blueprint(search_bp)
app.register_blueprint(bulk_bp)

@app.route('/admin/add_ghazal')
def redirect_add_ghazal():
    return redirect(url_for('ghazals.add_ghazal'))

@app.route('/view/<int:text_id>')
def redirect_view(text_id):
    return redirect(url_for('ghazals.view_ghazal', text_id=text_id))

@app.context_processor
def inject_stats():
    return dict(stats=get_stats())

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500

if __name__ == '__main__':
    app.run(debug=True)