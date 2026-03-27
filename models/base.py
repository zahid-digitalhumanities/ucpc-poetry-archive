import psycopg2
import psycopg2.extras
from config import DB_CONFIG

def get_db():
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