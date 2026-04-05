from models.base import get_db

def fetch_all_poets():
    conn = get_db()
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
    """Fetch a single poet by ID."""
    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT id, name, name_urdu, bio_english, bio_urdu,
                   birth_year, death_year
            FROM poets
            WHERE id = %s
        """, (poet_id,))
        return cur.fetchone()
    finally:
        cur.close()
        conn.close()

def fetch_poets_with_sample():
    """Fetch all poets with one sample ghazal text for home page preview."""
    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT 
                p.id,
                p.name,
                p.name_urdu,
                t.text_urdu
            FROM poets p
            LEFT JOIN (
                SELECT poet_id, text_urdu,
                       ROW_NUMBER() OVER (PARTITION BY poet_id ORDER BY id) AS rn
                FROM texts
                WHERE text_urdu IS NOT NULL
            ) t ON p.id = t.poet_id AND t.rn = 1
            WHERE t.text_urdu IS NOT NULL
            ORDER BY p.name ASC
        """)
        return cur.fetchall()
    finally:
        cur.close()
        conn.close()