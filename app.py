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

if __name__ == '__main__':
    app.run(debug=True)