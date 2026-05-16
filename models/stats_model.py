from models.base import get_db   # or from models.ghazal_model import get_db

def get_stats():
    conn = get_db()
    try:
        cur = conn.cursor()

        # Poets
        cur.execute("SELECT COUNT(*) FROM poets")
        poets = cur.fetchone()['count']

        # Texts (ghazals + nazms)
        cur.execute("""
            SELECT column_name FROM information_schema.columns 
            WHERE table_name = 'texts' AND column_name = 'form'
        """)
        if cur.fetchone():
            cur.execute("SELECT COUNT(*) FROM texts WHERE form IN ('ghazal', 'nazm')")
        else:
            cur.execute("SELECT COUNT(*) FROM texts")
        texts = cur.fetchone()['count']

        # Verses
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