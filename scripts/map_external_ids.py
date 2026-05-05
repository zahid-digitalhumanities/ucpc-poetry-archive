# scripts/map_external_ids.py
import sys
import os
import json
import hashlib
import re
import glob

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from models.base import get_db_connection

# ================= CONFIGURATION =================
JSON_BASE_PATH = r"E:\dashboard\texts"   # <-- CHANGE to where your *_texts.json are
# If your texts are directly in E:\dashboard\texts, leave as is.
# If they are in subfolders, adjust glob pattern accordingly.

# ================= NORMALISATION =================
def normalize(text):
    if not text:
        return ""
    text = text.strip()
    text = re.sub(r'[،۔!؟,.;:]', '', text)   # remove punctuation
    text = re.sub(r'\s+', ' ', text)          # collapse spaces
    return text

def make_hash(text):
    return hashlib.md5(text.encode('utf-8')).hexdigest()

# ================= LOAD JSON =================
def load_json_mapping(json_path):
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    mapping = {}
    for item in data:
        ext_id = item.get("TEXT_ID")
        content = item.get("CONTENT", "")
        lines = [l.strip() for l in content.split('\n') if l.strip()]
        if len(lines) < 2:
            continue
        first_couplet = normalize(lines[0] + " " + lines[1])
        h = make_hash(first_couplet)
        mapping[h] = ext_id
    return mapping

# ================= MAIN =================
def map_all_json_files():
    conn = get_db_connection()
    cur = conn.cursor()

    # Ensure external_id column exists
    cur.execute("ALTER TABLE texts ADD COLUMN IF NOT EXISTS external_id TEXT;")
    conn.commit()

    # Load all first couplets from verses table (one per text_id)
    cur.execute("""
        SELECT DISTINCT ON (text_id)
            text_id,
            misra1_urdu,
            misra2_urdu
        FROM verses
        ORDER BY text_id, couplet_index
    """)
    verses_map = {}
    for row in cur.fetchall():
        tid = row['text_id']
        m1 = row['misra1_urdu']
        m2 = row['misra2_urdu']
        if not m1 or not m2:
            continue
        combined = normalize(m1 + " " + m2)
        h = make_hash(combined)
        verses_map[h] = tid
    print(f"✅ Loaded {len(verses_map)} unique first couplets from verses table.")

    # Find all JSON files
    json_pattern = os.path.join(JSON_BASE_PATH, "*_texts.json")
    json_files = glob.glob(json_pattern)
    if not json_files:
        print(f"❌ No JSON files found in {JSON_BASE_PATH}")
        return

    total_matched = 0
    for json_path in json_files:
        print(f"\n📂 Processing {os.path.basename(json_path)}...")
        json_map = load_json_mapping(json_path)
        print(f"   Loaded {len(json_map)} entries from JSON")

        matched = 0
        for h, ext_id in json_map.items():
            if h in verses_map:
                internal_id = verses_map[h]
                cur.execute("UPDATE texts SET external_id = %s WHERE id = %s", (ext_id, internal_id))
                matched += 1
        total_matched += matched
        print(f"   ✅ Matched {matched} / {len(json_map)}")

    conn.commit()
    cur.close()
    conn.close()
    print(f"\n🎉 TOTAL MATCHED: {total_matched} ghazals updated with external_id")

if __name__ == "__main__":
    map_all_json_files()