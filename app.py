from flask import Flask
from config import TEMPLATE_FOLDER, STATIC_FOLDER, SECRET_KEY

from routes.main import main_bp
from routes.ghazal import ghazal_bp

app = Flask(__name__,
            template_folder=TEMPLATE_FOLDER,
            static_folder=STATIC_FOLDER)

app.secret_key = SECRET_KEY

app.register_blueprint(main_bp)
app.register_blueprint(ghazal_bp)

if __name__ == "__main__":
    app.run(debug=True)