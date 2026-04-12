import os
import psycopg2
import psycopg2.extras

def get_db_connection():
    """Return a database connection using DATABASE_URL (Render) or local env vars."""
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        # Render.com uses DATABASE_URL with sslmode=require
        return psycopg2.connect(database_url, sslmode='require', cursor_factory=psycopg2.extras.RealDictCursor)
    else:
        # Local development – use defaults (password '123' as you said)
        return psycopg2.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            database=os.getenv('DB_NAME', 'ucpc_v3_db'),
            user=os.getenv('DB_USER', 'postgres'),
            password=os.getenv('DB_PASSWORD', '123'),   # default '123' for local
            port=os.getenv('DB_PORT', 5432),
            cursor_factory=psycopg2.extras.RealDictCursor
        )

# Alias for backward compatibility
get_db = get_db_connection
