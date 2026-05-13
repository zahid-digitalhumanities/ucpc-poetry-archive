import sys
import os
import hashlib
import math

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.base import get_db_connection
from modules.text_normalizer import normalize_urdu

def sha256(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()

conn = get_db_connection()
cur = conn.cursor()

# ------------------------------------------------------------
# 1. Fetch all verses ordered by text_id and couplet_index
# ------------------------------------------------------------
cur.execute("""
    SELECT
        v.text_id,
        v.couplet_index,
        COALESCE(v.misra1_urdu, '') AS misra1,
        COALESCE(v.misra2_urdu, '') AS misra2
    FROM verses v
    ORDER BY v.text_id, v.couplet_index
""")
rows = cur.fetchall()

# ------------------------------------------------------------
# 2. Build full text (preserve couplet boundaries with \n)
#    Normalize each verse before aggregation
# ------------------------------------------------------------
text_data = {}
for row in rows:
    tid = row['text_id']
    if tid not in text_data:
        text_data[tid] = {'verses': [], 'matla': None}

    # Normalize the whole couplet (both misras together)
    raw_couplet = f"{row['misra1']} {row['misra2']}".strip()
    norm_couplet = normalize_urdu(raw_couplet)
    if norm_couplet:   # skip completely empty couplets
        text_data[tid]['verses'].append(norm_couplet)

    # Matla = first non‑empty couplet
    if text_data[tid]['matla'] is None and norm_couplet:
        text_data[tid]['matla'] = norm_couplet

# ------------------------------------------------------------
# 3. Generate hashes, skip completely empty texts
# ------------------------------------------------------------
for tid, data in text_data.items():
    if not data['verses']:
        continue   # no valid content

    full_text = "\n".join(data['verses'])   # preserve verse boundaries
    matla = data['matla'] or ""

    full_text_norm = full_text   # already normalized per verse
    matla_norm = matla

    full_hash = sha256(full_text_norm) if full_text_norm else None
    matla_hash = sha256(matla_norm) if matla_norm else None

    cur.execute("""
        UPDATE texts
        SET normalized_text = %s,
            full_text_hash = %s,
            matla_hash = %s,
            normalized_matla = %s
        WHERE id = %s
    """, (full_text_norm, full_hash, matla_hash, matla_norm, tid))

conn.commit()

# ------------------------------------------------------------
# 4. Auto‑mark canonical (keep smallest id per full_text_hash)
# ------------------------------------------------------------
cur.execute("""
    UPDATE texts t
    SET is_canonical = FALSE
    FROM (
        SELECT MIN(id) AS keep_id, full_text_hash
        FROM texts
        WHERE full_text_hash IS NOT NULL
        GROUP BY full_text_hash
        HAVING COUNT(*) > 1
    ) d
    WHERE t.full_text_hash = d.full_text_hash
      AND t.id != d.keep_id
""")
conn.commit()

# ------------------------------------------------------------
# 5. Add integrity score and flags columns (if not exist)
# ------------------------------------------------------------
cur.execute("""
    ALTER TABLE texts
    ADD COLUMN IF NOT EXISTS integrity_score FLOAT DEFAULT 1.0
""")
cur.execute("""
    ALTER TABLE texts
    ADD COLUMN IF NOT EXISTS integrity_flags TEXT[] DEFAULT '{}'
""")
conn.commit()

# Simple integrity scoring (example)
cur.execute("""
    UPDATE texts
    SET integrity_score = 1.0,
        integrity_flags = '{}'
    WHERE integrity_score IS NULL
""")
conn.commit()

# Mark duplicates with low score and flag
cur.execute("""
    UPDATE texts
    SET integrity_score = 0.3,
        integrity_flags = array_append(integrity_flags, 'duplicate')
    WHERE is_canonical = FALSE
""")
conn.commit()

cur.close()
conn.close()

print(f"Hashes generated for {len(text_data)} texts. Canonical flags and integrity scores updated.")