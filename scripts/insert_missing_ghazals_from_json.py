# scripts/insert_missing_ghazals_from_json.py
import sys
import os
import json
import re
import hashlib
import glob
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from models.base import get_db_connection

# ================= CONFIGURATION =================
JSON_BASE_PATH = r"E:\dashboard\texts"   # <-- your JSON folder
POET_NAME_MAP = {
    "faiz": "Faiz Ahmed Faiz",
    "fraz": "Ahmed Faraz",
    "ghalib": "Mirza Ghalib",
    "iqbal": "Allama Iqbal",
    "kazmi": "Nasir Kazmi",
    "mir": "Mir Taqi Mir",
    "noshi": "Noshi Gilani",
    "parveen": "Parveen Shakir",
    "wasi": "Wasi Shah"
}

# ================= NORMALISATION =================
def normalize_line(line):
    if not line:
        return ""
    line = line.strip()
    line = re.sub(r'[،۔!؟,.;:]', '', line)
    line = re.sub(r'\s+', ' ', line)
    return line

def make_hash(text):
    return hashlib.md5(text.encode('utf-8')).hexdigest()

def first_couplet_hash(content):
    lines = [l.strip() for l in content.split('\n') if l.strip()]
    if len(lines) < 2:
        return None
    combined = normalize_line(lines[0]) + " " + normalize_line(lines[1])
    return make_hash(combined)

# ================= GET POET ID =================
def get_poet_id(poet_name):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id FROM poets WHERE name = %s", (poet_name,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row['id'] if row else None

# ================= INSERT GHAZAL (FIXED) =================
def insert_ghazal(conn, poet_id, title_ur, content, ext_id, title_en, translation_en):
    cur = conn.cursor()
    # Generate public_id from external_id (replace _ with -) or fallback
    if ext_id:
        public_id = ext_id.replace('_', '-')
    else:
        public_id = f"temp_{poet_id}_{int(time.time())}"
    
    cur.execute("""
        INSERT INTO texts (poet_id, title_urdu, text_urdu, external_id, title_english, translation_english, public_id, created_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())
        RETURNING id
    """, (poet_id, title_ur, content, ext_id, title_en, translation_en, public_id))
    text_id = cur.fetchone()['id']
    
    # Insert verses
    lines = [l.strip() for l in content.split('\n') if l.strip()]
    for idx in range(0, len(lines), 2):
        misra1 = lines[idx]
        misra2 = lines[idx+1] if idx+1 < len(lines) else ""
        couplet_index = (idx // 2) + 1
        cur.execute("""
            INSERT INTO verses (text_id, couplet_index, misra1_urdu, misra2_urdu)
            VALUES (%s, %s, %s, %s)
        """, (text_id, couplet_index, misra1, misra2))
    
    conn.commit()
    cur.close()
    return text_id

# ================= MAIN =================
def main():
    conn = get_db_connection()
    cur = conn.cursor()

    # Add required columns if they don't exist
    cur.execute("ALTER TABLE texts ADD COLUMN IF NOT EXISTS external_id TEXT;")
    cur.execute("ALTER TABLE texts ADD COLUMN IF NOT EXISTS title_english TEXT;")
    cur.execute("ALTER TABLE texts ADD COLUMN IF NOT EXISTS translation_english TEXT;")
    # Add provenance columns
    cur.execute("ALTER TABLE texts ADD COLUMN IF NOT EXISTS source TEXT;")
    cur.execute("ALTER TABLE texts ADD COLUMN IF NOT EXISTS composition_date TEXT;")
    cur.execute("ALTER TABLE texts ADD COLUMN IF NOT EXISTS source_url TEXT;")
    cur.execute("ALTER TABLE texts ADD COLUMN IF NOT EXISTS verification_status TEXT;")
    # Add annotation columns to poetic_features
    cur.execute("ALTER TABLE poetic_features ADD COLUMN IF NOT EXISTS ttr FLOAT;")
    cur.execute("ALTER TABLE poetic_features ADD COLUMN IF NOT EXISTS sentiment TEXT;")
    cur.execute("ALTER TABLE poetic_features ADD COLUMN IF NOT EXISTS rhyme_patterns TEXT;")
    cur.execute("ALTER TABLE poetic_features ADD COLUMN IF NOT EXISTS annotation_notes TEXT;")
    conn.commit()

    # Build existing hash map from verses table
    cur.execute("""
        SELECT DISTINCT ON (text_id) text_id, misra1_urdu, misra2_urdu
        FROM verses
        ORDER BY text_id, couplet_index
    """)
    existing_map = {}
    for row in cur.fetchall():
        tid = row['text_id']
        m1 = row['misra1_urdu']
        m2 = row['misra2_urdu']
        if m1 and m2:
            h = make_hash(normalize_line(m1) + " " + normalize_line(m2))
            existing_map[h] = tid
    print(f"📊 Loaded {len(existing_map)} existing first couplet hashes.")

    json_files = glob.glob(os.path.join(JSON_BASE_PATH, "*_texts.json"))
    total_inserted = 0
    total_updated = 0

    for json_path in json_files:
        poet_key = os.path.basename(json_path).replace("_texts.json", "")
        poet_name = POET_NAME_MAP.get(poet_key)
        if not poet_name:
            print(f"⚠️ Unknown poet key: {poet_key}, skipping {json_path}")
            continue
        poet_id = get_poet_id(poet_name)
        if not poet_id:
            print(f"❌ Poet '{poet_name}' not found in DB. Skipping {json_path}")
            continue

        print(f"\n📂 Processing {poet_key} ({poet_name}) ...")
        with open(json_path, 'r', encoding='utf-8') as f:
            records = json.load(f)

        for rec in records:
            ext_id = rec.get('TEXT_ID')
            title_ur = rec.get('TITLE_UR', '')
            content = rec.get('CONTENT', '')
            title_en = rec.get('TITLE_EN', '')
            translation_en = rec.get('TRANSLATION_EN', '')
            if not content:
                continue

            h = first_couplet_hash(content)
            if not h:
                print(f"  ⚠️ Could not extract first couplet for {ext_id}")
                continue

            if h in existing_map:
                # Update existing ghazal
                tid = existing_map[h]
                cur.execute("""
                    UPDATE texts
                    SET external_id = %s, title_english = %s, translation_english = %s
                    WHERE id = %s
                """, (ext_id, title_en, translation_en, tid))
                total_updated += 1
                print(f"  ✅ Updated existing: {ext_id} -> text_id {tid}")
            else:
                # Insert new ghazal
                tid = insert_ghazal(conn, poet_id, title_ur, content, ext_id, title_en, translation_en)
                # Add to existing_map for future duplicates
                existing_map[h] = tid
                total_inserted += 1
                print(f"  🆕 Inserted new: {ext_id} -> text_id {tid}")

    conn.commit()
    cur.close()
    conn.close()
    print(f"\n🎉 Done! Inserted {total_inserted} new ghazals, updated {total_updated} existing ghazals.")

if __name__ == "__main__":
    main()