import os

from flask import Flask, render_template, jsonify

from config import config

# =====================================================
# APP
# =====================================================

app = Flask(__name__)

env = os.getenv("FLASK_ENV", "production")

app.config.from_object(config["production"])

# =====================================================
# IMPORT ROUTES
# =====================================================

from routes.main_routes import main_bp
from routes.poets_routes import poets_bp
from routes.ghazals_routes import ghazals_bp

# =====================================================
# REGISTER
# =====================================================

app.register_blueprint(main_bp)

app.register_blueprint(
    poets_bp,
    url_prefix="/poets"
)

app.register_blueprint(
    ghazals_bp,
    url_prefix="/ghazals"
)

# =====================================================
# HEALTH
# =====================================================

@app.route("/health")
def health():

    return jsonify({
        "status": "ok",
        "project": "UCPC"
    })

# =====================================================
# ERROR
# =====================================================

@app.errorhandler(404)
def not_found(e):

    return render_template("404.html"), 404

@app.errorhandler(500)
def server_error(e):

    return render_template("500.html"), 500

# =====================================================
# RUN
# =====================================================

if __name__ == "__main__":

    port = int(
        os.environ.get("PORT", 10000)
    )

    app.run(
        host="0.0.0.0",
        port=port,
        debug=False
    )