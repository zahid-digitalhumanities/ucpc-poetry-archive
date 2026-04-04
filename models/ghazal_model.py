# models/ghazal_model.py

import uuid
import hashlib
from models.base import get_db_connection


def get_db():
    return get_db_connection()


def get_stats():
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM poets")
            poets = cur.fetchone()['count']

            cur.execute("SELECT COUNT(*) FROM texts WHERE form = 'ghazal'")
            texts = cur.fetchone()['count']

            cur.execute("SELECT COUNT(*) FROM verses")
            verses = cur.fetchone()['count']

    return {
        'total_poets': poets,
        'total_ghazals': texts,
        'texts': texts,
        'total_verses': verses,
        'verses': verses
    }


def fetch_texts_by_poet(poet_id):
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, public_id, title_urdu, title_english, verse_count
                FROM texts
                WHERE poet_id = %s AND form = 'ghazal'
                ORDER BY id
            """, (poet_id,))
            return cur.fetchall()