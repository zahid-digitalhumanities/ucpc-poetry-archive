from db import get_db_connection

def get_ghazal(id):
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM texts WHERE id=%s", (id,))
            return cur.fetchone()

def get_verses(id):
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT * FROM verses
                WHERE text_id=%s
                ORDER BY couplet_index
            """, (id,))
            return cur.fetchall()