# models/base.py
import os
import psycopg2
import psycopg2.extras

def get_db_connection():
    """Return a database connection using DATABASE_URL environment variable."""
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        return psycopg2.connect(database_url, sslmode='require', cursor_factory=psycopg2.extras.RealDictCursor)
    else:
        # Fallback to local config
        from config import DB_CONFIG
        if 'dsn' in DB_CONFIG:
            return psycopg2.connect(DB_CONFIG['dsn'], cursor_factory=psycopg2.extras.RealDictCursor)
        else:
            return psycopg2.connect(
                dbname=DB_CONFIG['dbname'],
                user=DB_CONFIG['user'],
                password=DB_CONFIG['password'],
                host=DB_CONFIG['host'],
                port=DB_CONFIG['port'],
                cursor_factory=psycopg2.extras.RealDictCursor
            )

# Alias for backward compatibility
get_db = get_db_connection