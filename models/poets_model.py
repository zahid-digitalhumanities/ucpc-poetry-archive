from models.base import get_db_connection

def fetch_all_poets():
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT p.id, p.name, p.name_urdu, COUNT(t.id) as ghazal_count
                FROM poets p
                LEFT JOIN texts t ON t.poet_id = p.id AND t.form = 'ghazal'
                GROUP BY p.id ORDER BY p.name
            """)
            rows = cur.fetchall()
            return [dict(row) for row in rows]

# Alias for main_routes
fetch_poets_with_sample = fetch_all_poets

def get_all_poets():
    return fetch_all_poets()

def fetch_poet_by_id(poet_id):
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, name, name_urdu, bio_english, birth_year, death_year, wikipedia_url
                FROM poets WHERE id = %s
            """, (poet_id,))
            row = cur.fetchone()
            return dict(row) if row else None

def get_texts_with_first_verses(poet_id):
    """Original non‑paginated version (kept for compatibility)"""
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, verse_count
                FROM texts
                WHERE poet_id = %s AND form = 'ghazal'
                ORDER BY id
            """, (poet_id,))
            texts_rows = cur.fetchall()
            result = []
            for text_row in texts_rows:
                text_id = text_row['id']
                verse_count = text_row['verse_count'] or 0
                cur.execute("""
                    SELECT misra1_urdu, misra2_urdu
                    FROM verses
                    WHERE text_id = %s
                    ORDER BY couplet_index ASC
                    LIMIT 2
                """, (text_id,))
                verses_rows = cur.fetchall()
                first_verse = None
                second_verse = None
                if len(verses_rows) >= 1:
                    first_verse = {'misra1_urdu': verses_rows[0]['misra1_urdu'] or '', 'misra2_urdu': verses_rows[0]['misra2_urdu'] or ''}
                if len(verses_rows) >= 2:
                    second_verse = {'misra1_urdu': verses_rows[1]['misra1_urdu'] or '', 'misra2_urdu': verses_rows[1]['misra2_urdu'] or ''}
                result.append({'id': text_id, 'verse_count': verse_count, 'first_verse': first_verse, 'second_verse': second_verse})
            return result

def get_texts_with_first_verses_paginated(poet_id, page=1, per_page=12):
    """Paginated version – returns (texts_list, total_count)"""
    offset = (page - 1) * per_page
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            # Total count
            cur.execute("""
                SELECT COUNT(*) FROM texts
                WHERE poet_id = %s AND form = 'ghazal'
            """, (poet_id,))
            total = cur.fetchone()['count']

            # Paginated texts
            cur.execute("""
                SELECT id, verse_count
                FROM texts
                WHERE poet_id = %s AND form = 'ghazal'
                ORDER BY id
                LIMIT %s OFFSET %s
            """, (poet_id, per_page, offset))
            texts_rows = cur.fetchall()

            result = []
            for text_row in texts_rows:
                text_id = text_row['id']
                verse_count = text_row['verse_count'] or 0
                cur.execute("""
                    SELECT misra1_urdu, misra2_urdu
                    FROM verses
                    WHERE text_id = %s
                    ORDER BY couplet_index ASC
                    LIMIT 2
                """, (text_id,))
                verses_rows = cur.fetchall()
                first_verse = None
                second_verse = None
                if len(verses_rows) >= 1:
                    first_verse = {'misra1_urdu': verses_rows[0]['misra1_urdu'] or '', 'misra2_urdu': verses_rows[0]['misra2_urdu'] or ''}
                if len(verses_rows) >= 2:
                    second_verse = {'misra1_urdu': verses_rows[1]['misra1_urdu'] or '', 'misra2_urdu': verses_rows[1]['misra2_urdu'] or ''}
                result.append({'id': text_id, 'verse_count': verse_count, 'first_verse': first_verse, 'second_verse': second_verse})
            return result, total

def fetch_poet_with_first_verses(poet_id):
    poet = fetch_poet_by_id(poet_id)
    if not poet:
        return None
    poet['texts'] = get_texts_with_first_verses(poet_id)
    return poet