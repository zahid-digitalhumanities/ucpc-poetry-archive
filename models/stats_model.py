from db import get_db_connection

def get_stats():
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM poets")
            poets = cur.fetchone()[0]

            cur.execute("SELECT COUNT(*) FROM texts")
            ghazals = cur.fetchone()[0]

            return {"poets": poets, "ghazals": ghazals}