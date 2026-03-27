import os

# Database Configuration
DB_CONFIG = {
    'dbname': 'ucpc_v3_db',
    'user': 'postgres',
    'password': '123',
    'host': 'localhost',
    'port': '5432'
}

# Flask Configuration
SECRET_KEY = 'your-secret-key-here-change-in-production'
MAX_CONTENT_LENGTH = 500 * 1024 * 1024  # 500MB

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_FOLDER = os.path.join(BASE_DIR, 'templates')
STATIC_FOLDER = os.path.join(BASE_DIR, 'static')
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
