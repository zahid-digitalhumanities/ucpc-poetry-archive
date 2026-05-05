import sys
import os
import csv

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from models.base import get_db_connection

# ================= CLEAN FUNCTION =================
def clean_text(text):
    if not text:
        return ""
    text = text.replace('\n', ' ')
    text = text.replace('،', '').replace('۔', '')
    text = ' '.join(text.split())
    return text.strip()

# ================= FETCH DATA =================
conn = get_db_connection()
cur = conn.cursor()

cur.execute("""
    SELECT 
        t.id as text_id,
        t.poet_id,
        v.misra1_urdu,
        v.misra2_urdu,
        v.couplet_index
    FROM texts t
    JOIN verses v ON t.id = v.text_id
    WHERE t.poet_id IS NOT NULL
    ORDER BY t.id, v.couplet_index
""")

rows = cur.fetchall()
cur.close()
conn.close()

# ================= BUILD FULL GHAZALS =================
ghazals = {}

for row in rows:
    text_id = row['text_id']
    poet_id = row['poet_id']

    if text_id not in ghazals:
        ghazals[text_id] = {
            "poet_id": poet_id,
            "lines": []
        }

    if row['misra1_urdu']:
        ghazals[text_id]["lines"].append(row['misra1_urdu'])
    if row['misra2_urdu']:
        ghazals[text_id]["lines"].append(row['misra2_urdu'])

# ================= WRITE CSV to scripts/ folder =================
# Get the project root (two levels up from this script)
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
output_dir = os.path.join(project_root, 'scripts')
os.makedirs(output_dir, exist_ok=True)
output_path = os.path.join(output_dir, "training_data.csv")

seen_texts = set()
total = 0

with open(output_path, 'w', encoding='utf-8', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['text_urdu', 'poet_id'])

    for g in ghazals.values():
        full_text = clean_text(" ".join(g["lines"]))

        # ❌ skip weak ghazals
        if len(full_text.split()) < 20:
            continue

        # ❌ remove duplicates
        if full_text in seen_texts:
            continue

        seen_texts.add(full_text)

        writer.writerow([full_text, g["poet_id"]])
        total += 1

print(f"✅ training_data.csv created at: {output_path}")
print(f"📊 Total clean ghazals: {total}")