import os
import psycopg2
import psycopg2.extras

def get_db():
    """Return a database connection. Uses DATABASE_URL environment variable if present,
    otherwise falls back to config.py for local development."""
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        return psycopg2.connect(database_url, cursor_factory=psycopg2.extras.RealDictCursor)
    else:
        # Local development – use config.py
        from config import DB_CONFIG
        return psycopg2.connect(
            dbname=DB_CONFIG['dbname'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password'],
            host=DB_CONFIG['host'],
            port=DB_CONFIG['port'],
            cursor_factory=psycopg2.extras.RealDictCursor
        )

def get_cursor(conn):
    """Return a cursor from an existing connection (already RealDictCursor)."""
    return conn.cursor()