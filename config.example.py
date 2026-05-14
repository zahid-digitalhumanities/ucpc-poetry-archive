# config.example.py
"""
UCPC Configuration Template
Copy this file to config.py and add your credentials
config.py is ignored by git for security
"""

import os

# Database Configuration
DATABASE_URL = os.environ.get('DATABASE_URL')

if DATABASE_URL:
    DB_CONFIG = {'dsn': DATABASE_URL}
else:
    # LOCAL DEVELOPMENT - Update these values
    DB_CONFIG = {
        'dbname': 'your_database_name',
        'user': 'your_username',
        'password': 'your_password',
        'host': 'localhost',
        'port': '5432'
    }

# Flask Configuration
SECRET_KEY = os.environ.get('SECRET_KEY', 'change-this-to-random-secret-key')
MAX_CONTENT_LENGTH = 500 * 1024 * 1024

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_FOLDER = os.path.join(BASE_DIR, 'templates')
STATIC_FOLDER = os.path.join(BASE_DIR, 'static')
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')