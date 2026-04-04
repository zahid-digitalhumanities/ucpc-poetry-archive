# models/poets_model.py
from models.base import get_db_connection

def fetch_all_poets():
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT p.id, p.name, p.name_urdu, p.birth_year, p.death_year,
                   COUNT(t.id) AS poem_count
            FROM poets p
            LEFT JOIN texts t ON t.poet_id = p.id AND t.form IN ('ghazal', 'nazm')
            GROUP BY p.id
            ORDER BY p.name
        """)
        return cur.fetchall()
    finally:
        cur.close()
        conn.close()

def fetch_poet_by_id(poet_id):
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT id, name, name_urdu, bio_english, bio_urdu,
                   birth_year, death_year
            FROM poets WHERE id = %s
        """, (poet_id,))
        return cur.fetchone()
    finally:
        cur.close()
        conn.close()