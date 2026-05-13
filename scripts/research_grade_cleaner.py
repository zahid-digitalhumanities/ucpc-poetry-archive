# scripts/research_grade_cleaner.py

import sys
import os
import hashlib
from collections import defaultdict

# =========================================================
# ADD PROJECT ROOT
# =========================================================
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.base import get_db_connection
from modules.text_normalizer import normalize_urdu

# =========================================================
# HELPERS
# =========================================================
def sha256(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

def ensure_columns(cur):
    """Create integrity columns if they don't exist."""
    cur.execute("""
        SELECT column_name
        FROM information_schema.columns
        WHERE table_name = 'texts' AND column_name = 'is_deleted'
    """)
    if not cur.fetchone():
        cur.execute("ALTER TABLE texts ADD COLUMN is_deleted BOOLEAN DEFAULT FALSE")
    cur.execute("""
        SELECT column_name
        FROM information_schema.columns
        WHERE table_name = 'texts' AND column_name = 'integrity_status'
    """)
    if not cur.fetchone():
        cur.execute("ALTER TABLE texts ADD COLUMN integrity_status VARCHAR(20) DEFAULT 'clean'")
    cur.execute("""
        SELECT column_name
        FROM information_schema.columns
        WHERE table_name = 'texts' AND column_name = 'canonical_parent'
    """)
    if not cur.fetchone():
        cur.execute("ALTER TABLE texts ADD COLUMN canonical_parent INTEGER")

# =========================================================
# DATABASE CONNECTION
# =========================================================
conn = get_db_connection()
cur = conn.cursor()
ensure_columns(cur)
conn.commit()

print("\n==============================")
print(" UCPC RESEARCH GRADE CLEANER ")
print("==============================\n")

# =========================================================
# STEP 1 — FETCH ALL GHAZALS
# =========================================================
print("Fetching corpus...")
cur.execute("""
    SELECT
        t.id,
        t.poet_id,
        p.name AS poet_name,
        t.title_urdu,
        v.couplet_index,
        COALESCE(v.misra1_urdu, '') AS misra1,
        COALESCE(v.misra2_urdu, '') AS misra2
    FROM texts t
    JOIN poets p ON p.id = t.poet_id
    LEFT JOIN verses v ON v.text_id = t.id
    WHERE t.form = 'ghazal' AND COALESCE(t.is_deleted, FALSE) = FALSE
    ORDER BY t.id, v.couplet_index
""")
rows = cur.fetchall()
print(f"Loaded {len(rows)} verse rows.\n")

# =========================================================
# STEP 2 — BUILD FULL TEXTS
# =========================================================
print("Building normalized texts...")
texts = {}
for row in rows:
    tid = row['id']
    if tid not in texts:
        texts[tid] = {
            'text_id': tid,
            'poet_id': row['poet_id'],
            'poet_name': row['poet_name'],
            'title_urdu': row['title_urdu'],
            'verses': [],
            'matla': None
        }
    verse = f"{row['misra1']} {row['misra2']}".strip()
    if verse:
        texts[tid]['verses'].append(verse)
    if texts[tid]['matla'] is None and verse:
        texts[tid]['matla'] = verse

print(f"Prepared {len(texts)} ghazals.\n")

# =========================================================
# STEP 3 — GENERATE HASHES (and store in DB)
# =========================================================
print("Generating hashes...")
full_hash_map = defaultdict(list)
matla_hash_map = defaultdict(list)

for tid, data in texts.items():
    full_text = " ".join(data['verses']).strip()
    matla = (data['matla'] or '').strip()
    full_norm = normalize_urdu(full_text) if full_text else ""
    matla_norm = normalize_urdu(matla) if matla else ""
    full_hash = sha256(full_norm) if full_norm else None
    matla_hash = sha256(matla_norm) if matla_norm else None

    cur.execute("""
        UPDATE texts
        SET normalized_text = %s,
            full_text_hash = %s,
            matla_hash = %s,
            normalized_matla = %s
        WHERE id = %s
    """, (full_norm, full_hash, matla_hash, matla_norm, tid))

    if full_hash:
        full_hash_map[full_hash].append(tid)
    if matla_hash:
        matla_hash_map[matla_hash].append(tid)

conn.commit()
print("Hashes generated.\n")

# =========================================================
# STEP 4 — EXACT DUPLICATES (same full text, same poet)
# =========================================================
print("==============================")
print(" EXACT DUPLICATE CLEANING ")
print("==============================\n")

exact_removed = 0
for h, ids in full_hash_map.items():
    if len(ids) <= 1:
        continue

    group = []
    for tid in ids:
        d = texts[tid]
        group.append({
            'id': tid,
            'poet_id': d['poet_id'],
            'poet_name': d['poet_name'],
            'verse_count': len(d['verses'])
        })

    group.sort(key=lambda x: (-x['verse_count'], x['id']))
    keep = group[0]
    print(f"\nCanonical: {keep['id']} ({keep['poet_name']})")

    for g in group[1:]:
        dup_id = g['id']
        if g['poet_id'] == keep['poet_id']:
            cur.execute("""
                UPDATE texts
                SET is_deleted = TRUE,
                    integrity_status = 'merged',
                    canonical_parent = %s
                WHERE id = %s
            """, (keep['id'], dup_id))
            exact_removed += 1
            print(f"  MERGED {dup_id} -> {keep['id']}")
        else:
            # Different poet → attribution conflict (keep both, flag)
            cur.execute("""
                UPDATE texts
                SET integrity_status = 'conflict',
                    canonical_parent = %s
                WHERE id = %s AND integrity_status NOT IN ('merged', 'disputed')
            """, (keep['id'], dup_id))
            print(f"  CONFLICT {dup_id} ({g['poet_name']})")

conn.commit()

# =========================================================
# STEP 5 — MATLA COLLISION CLEANING (aggressive)
# =========================================================
print("\n==============================")
print(" MATLA COLLISION CLEANING ")
print("==============================\n")

matla_removed = 0
for h, ids in matla_hash_map.items():
    if len(ids) <= 1:
        continue

    group = []
    for tid in ids:
        d = texts[tid]
        group.append({
            'id': tid,
            'poet_id': d['poet_id'],
            'poet_name': d['poet_name'],
            'verse_count': len(d['verses'])
        })

    # Choose canonical: higher verse count, then lower ID
    group.sort(key=lambda x: (-x['verse_count'], x['id']))
    keep = group[0]

    print(f"\nKeeping canonical matla: {keep['id']} ({keep['poet_name']})")

    for g in group[1:]:
        dup_id = g['id']
        cur.execute("""
            UPDATE texts
            SET is_deleted = TRUE,
                integrity_status = 'matla_removed',
                canonical_parent = %s
            WHERE id = %s
        """, (keep['id'], dup_id))
        matla_removed += 1
        print(f"  REMOVED {dup_id} ({g['poet_name']})")

conn.commit()

# =========================================================
# FINAL REPORT
# =========================================================
print("\n==============================")
print(" CLEANING COMPLETE ")
print("==============================\n")
print(f"Total Ghazals processed:  {len(texts)}")
print(f"Exact Duplicates Merged:   {exact_removed}")
print(f"Matla Duplicates Removed:  {matla_removed}")

cur.execute("SELECT COUNT(*) FROM texts WHERE is_deleted = FALSE AND form = 'ghazal'")
remaining = cur.fetchone()['count']
print(f"\nRemaining active ghazals: {remaining}")

print("\nCorpus integrity improved successfully.\n")
cur.close()
conn.close()