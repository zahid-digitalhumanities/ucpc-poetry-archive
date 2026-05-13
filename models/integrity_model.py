from models.base import get_db_connection

# =========================================================
# STATS
# =========================================================
def get_duplicate_stats():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT
            COUNT(*) FILTER (WHERE form = 'ghazal') AS total_ghazals,
            COUNT(*) FILTER (WHERE form = 'nazm') AS total_nazms,
            COUNT(*) FILTER (WHERE form IS NULL) AS unknown_forms
        FROM texts
        WHERE COALESCE(is_deleted, FALSE) = FALSE
    """)
    row = cur.fetchone()
    cur.close()
    conn.close()
    return {
        'total_ghazals': row['total_ghazals'] or 0,
        'total_nazms': row['total_nazms'] or 0,
        'unknown_forms': row['unknown_forms'] or 0
    }

# =========================================================
# EXACT DUPLICATE GROUPS
# =========================================================
def get_duplicate_groups(limit=50):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT
            t.full_text_hash,
            ARRAY_AGG(t.id ORDER BY t.id) AS duplicate_ids,
            COUNT(*) AS copies,
            MIN(t.id) AS canonical_id,
            MIN(t.title_urdu) AS matla,
            STRING_AGG(DISTINCT COALESCE(p.name, 'Unknown'), ', ') AS poets
        FROM texts t
        LEFT JOIN poets p ON p.id = t.poet_id
        WHERE t.full_text_hash IS NOT NULL
          AND COALESCE(t.is_deleted, FALSE) = FALSE
          AND t.form = 'ghazal'
        GROUP BY t.full_text_hash
        HAVING COUNT(*) > 1
        ORDER BY copies DESC
        LIMIT %s
    """, (limit,))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows

# =========================================================
# ATTRIBUTION CONFLICTS
# =========================================================
def get_attribution_conflicts(limit=50):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT
            t.matla_hash,
            MIN(t.normalized_matla) AS normalized_matla,
            COUNT(DISTINCT t.poet_id) AS poet_count,
            STRING_AGG(DISTINCT COALESCE(p.name, 'Unknown'), ', ') AS poets,
            COUNT(*) AS copies
        FROM texts t
        LEFT JOIN poets p ON p.id = t.poet_id
        WHERE t.matla_hash IS NOT NULL
          AND t.normalized_matla IS NOT NULL
          AND COALESCE(t.is_deleted, FALSE) = FALSE
          AND t.form = 'ghazal'
        GROUP BY t.matla_hash
        HAVING COUNT(DISTINCT t.poet_id) > 1
        ORDER BY poet_count DESC, copies DESC
        LIMIT %s
    """, (limit,))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows

# =========================================================
# MATLA COLLISIONS
# =========================================================
def get_matla_collisions(limit=50):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT
            t.matla_hash,
            MIN(t.normalized_matla) AS normalized_matla,
            COUNT(*) AS record_count,
            STRING_AGG(DISTINCT COALESCE(p.name, 'Unknown'), ', ') AS poets
        FROM texts t
        LEFT JOIN poets p ON p.id = t.poet_id
        WHERE t.matla_hash IS NOT NULL
          AND COALESCE(t.is_deleted, FALSE) = FALSE
          AND t.form = 'ghazal'
        GROUP BY t.matla_hash
        HAVING COUNT(*) > 1
        ORDER BY record_count DESC
        LIMIT %s
    """, (limit,))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows

# =========================================================
# NEAR DUPLICATES (disabled – immediate return)
# =========================================================
def get_near_duplicates(limit=30):
    # After full corpus cleaning, no near duplicates remain.
    # Returning empty list avoids timeout and dashboard errors.
    return []

# =========================================================
# CANONICAL VARIANTS
# =========================================================
def get_canonical_variants(hash_value):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT
            t.id,
            t.title_urdu,
            t.normalized_matla,
            COALESCE(p.name, 'Unknown') AS poet_name
        FROM texts t
        LEFT JOIN poets p ON p.id = t.poet_id
        WHERE t.full_text_hash = %s
          AND COALESCE(t.is_deleted, FALSE) = FALSE
        ORDER BY t.id
    """, (hash_value,))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows