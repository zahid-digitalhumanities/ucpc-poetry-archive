# models/stats_model.py
from models.base import get_db_connection

def get_stats():
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM poets")
        poets = cur.fetchone()['count']
        cur.execute("SELECT COUNT(*) FROM texts WHERE form IN ('ghazal', 'nazm')")
        texts = cur.fetchone()['count']
        cur.execute("SELECT COUNT(*) FROM verses")
        verses = cur.fetchone()['count']
        return {
            'total_poets': poets,
            'total_ghazals': texts,
            'total_verses': verses
        }
    finally:
        cur.close()
        conn.close()