from models.db import get_db

class PosterModel:
    """Database access for poster data"""

    @staticmethod
    def get_ghazal_data(text_id):
        """Fetch ghazal metadata (poet name, title_urdu, views, etc.)"""
        conn = get_db()
        cur = conn.cursor()

        cur.execute("""
            SELECT t.id, t.verse_count, t.views, t.poet_id, t.title_urdu,
                   p.name as poet_name, p.name_urdu as poet_name_urdu
            FROM texts t
            LEFT JOIN poets p ON t.poet_id = p.id
            WHERE t.id = %s
        """, (text_id,))
        ghazal = cur.fetchone()
        cur.close()
        conn.close()
        return ghazal

    @staticmethod
    def get_verses(text_id, limit=4):
        """Fetch verses for poster (first `limit` couplets)"""
        conn = get_db()
        cur = conn.cursor()
        cur.execute("""
            SELECT misra1_urdu, misra2_urdu, couplet_index
            FROM verses
            WHERE text_id = %s
            ORDER BY couplet_index ASC
            LIMIT %s
        """, (text_id, limit))
        verses = cur.fetchall()
        cur.close()
        conn.close()
        return verses

    @staticmethod
    def increment_views(text_id):
        """Increase the view counter for this ghazal"""
        conn = get_db()
        cur = conn.cursor()
        try:
            cur.execute("UPDATE texts SET views = COALESCE(views, 0) + 1 WHERE id = %s", (text_id,))
            conn.commit()
        except Exception:
            conn.rollback()
        finally:
            cur.close()
            conn.close()
