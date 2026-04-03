lfrom db import get_db_connection

def fetch_all_poets(limit=10):
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM poets LIMIT %s", (limit,))
            return cur.fetchall()