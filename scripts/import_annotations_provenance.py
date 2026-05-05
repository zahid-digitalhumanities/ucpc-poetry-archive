# scripts/import_annotations_provenance.py
import sys
import os
import json
import glob

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from models.base import get_db_connection

# ================= CONFIGURATION =================
ANNOTATION_PATH = r"E:\dashboard\annotations"
PROVENANCE_PATH = r"E:\dashboard\provenance"

# ================= IMPORT ANNOTATIONS =================
def import_annotations(cur, json_path):
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    count = 0
    for item in data:
        ext_id = item.get('TEXT_ID')
        if not ext_id:
            continue
        # Update poetic_features using external_id
        cur.execute("""
            UPDATE poetic_features
            SET ttr = %s,
                sentiment = %s,
                rhyme_patterns = %s,
                annotation_notes = %s
            WHERE text_id = (SELECT id FROM texts WHERE external_id = %s)
        """, (
            item.get('TTR'),
            item.get('SENTIMENT'),
            item.get('RHYME_PATTERNS'),
            item.get('notes'),
            ext_id
        ))
        count += 1
    print(f"  ✅ Imported annotations for {os.path.basename(json_path)}: {count} records")

# ================= IMPORT PROVENANCE =================
def import_provenance(cur, json_path):
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    count = 0
    for item in data:
        ext_id = item.get('TEXT_ID')
        if not ext_id:
            continue
        cur.execute("""
            UPDATE texts
            SET source = %s,
                composition_date = %s,
                source_url = %s,
                verification_status = %s
            WHERE external_id = %s
        """, (
            item.get('SOURCE'),
            item.get('COMPOSITION_DATE'),
            item.get('SOURCE_URL'),
            item.get('VERIFICATION_STATUS'),
            ext_id
        ))
        count += 1
    print(f"  ✅ Imported provenance for {os.path.basename(json_path)}: {count} records")

# ================= MAIN =================
def main():
    conn = get_db_connection()
    cur = conn.cursor()

    # Ensure required columns exist (already added, but safe)
    cur.execute("ALTER TABLE texts ADD COLUMN IF NOT EXISTS source TEXT;")
    cur.execute("ALTER TABLE texts ADD COLUMN IF NOT EXISTS composition_date TEXT;")
    cur.execute("ALTER TABLE texts ADD COLUMN IF NOT EXISTS source_url TEXT;")
    cur.execute("ALTER TABLE texts ADD COLUMN IF NOT EXISTS verification_status TEXT;")
    cur.execute("ALTER TABLE poetic_features ADD COLUMN IF NOT EXISTS ttr FLOAT;")
    cur.execute("ALTER TABLE poetic_features ADD COLUMN IF NOT EXISTS sentiment TEXT;")
    cur.execute("ALTER TABLE poetic_features ADD COLUMN IF NOT EXISTS rhyme_patterns TEXT;")
    cur.execute("ALTER TABLE poetic_features ADD COLUMN IF NOT EXISTS annotation_notes TEXT;")
    conn.commit()

    # Process annotation files
    ann_files = glob.glob(os.path.join(ANNOTATION_PATH, "*_annotations.json"))
    if ann_files:
        print("📂 Importing annotations...")
        for ann_path in ann_files:
            import_annotations(cur, ann_path)
    else:
        print("⚠️ No annotation files found in", ANNOTATION_PATH)

    # Process provenance files
    prov_files = glob.glob(os.path.join(PROVENANCE_PATH, "*_provenance.json"))
    if prov_files:
        print("\n📂 Importing provenance...")
        for prov_path in prov_files:
            import_provenance(cur, prov_path)
    else:
        print("⚠️ No provenance files found in", PROVENANCE_PATH)

    conn.commit()
    cur.close()
    conn.close()
    print("\n🎉 All annotations and provenance imported successfully!")

if __name__ == "__main__":
    main()