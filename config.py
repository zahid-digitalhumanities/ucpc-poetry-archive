# config.example.py
"""
UCPC Configuration Template
Copy this file to config.py and add your local credentials.
config.py is ignored by git for security.
"""

import os

# =========================================================
# DATABASE CONFIGURATION
# =========================================================

# For production (Render, Heroku, etc.) - use environment variable
DATABASE_URL = os.environ.get('DATABASE_URL')

if DATABASE_URL:
    # Production: use full connection string
    DB_CONFIG = {'dsn': DATABASE_URL}
else:
    # Local development: update with your credentials
    DB_CONFIG = {
        'dbname': 'ucpc_v3_db',      # Your database name
        'user': 'postgres',           # Your database username
        'password': 'your_password',  # CHANGE THIS to your actual password
        'host': 'localhost',
        'port': '5432'
    }

# =========================================================
# FLASK CONFIGURATION
# =========================================================

# Change this in production! Use a strong random key
SECRET_KEY = os.environ.get('SECRET_KEY', 'change-this-to-a-random-secret-key-in-production')

# Maximum upload size (500MB)
MAX_CONTENT_LENGTH = 500 * 1024 * 1024

# =========================================================
# PATH CONFIGURATION
# =========================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_FOLDER = os.path.join(BASE_DIR, 'templates')
STATIC_FOLDER = os.path.join(BASE_DIR, 'static')
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')

# =========================================================
# MODEL CONFIGURATION
# =========================================================

# Semantic search embedding model
EMBEDDING_MODEL = 'sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2'

# Poet classifier model version
POET_MODEL_VERSION = 'v9'

# =========================================================
# CORPUS CONFIGURATION
# =========================================================

CORPUS_VERSION = "1.2"
MIN_GHAZAL_LENGTH = 100
MAX_SEARCH_RESULTS = 50

# =========================================================
# SECURITY NOTES
# =========================================================
# 1. Never commit config.py to version control
# 2. Use environment variables for production secrets
# 3. Change default passwords immediately
# 4. Use a strong SECRET_KEY in production
