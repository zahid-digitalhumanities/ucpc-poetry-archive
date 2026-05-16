import os

# Database Configuration – use environment variable if available, else local
DATABASE_URL = os.environ.get('DATABASE_URL')
if DATABASE_URL:
    # For production, we'll use the full connection string
    DB_CONFIG = {'dsn': DATABASE_URL}
else:
    # Local development fallback
    DB_CONFIG = {
        'dbname': 'ucpc_v3_db',
        'user': 'postgres',
        'password': '123',
        'host': 'localhost',
        'port': '5432'
    }

# Flask Configuration
SECRET_KEY = os.environ.get('SECRET_KEY', 'your-secret-key-here-change-in-production')
MAX_CONTENT_LENGTH = 500 * 1024 * 1024  # 500MB

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_FOLDER = os.path.join(BASE_DIR, 'templates')
STATIC_FOLDER = os.path.join(BASE_DIR, 'static')
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')