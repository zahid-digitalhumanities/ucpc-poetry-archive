# models/contributors_model.py
from models.base import get_db

def get_all_contributors():
    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute("SELECT id, name FROM contributors ORDER BY name")
        return cur.fetchall()
    finally:
        cur.close()
        conn.close()