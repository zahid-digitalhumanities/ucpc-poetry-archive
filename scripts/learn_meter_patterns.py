# scripts/learn_meter_patterns.py
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.base import get_db_connection
from modules.meter import detect_meter
from collections import Counter

def main():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT t.id, v.misra1_urdu
        FROM texts t
        JOIN verses v ON t.id = v.text_id
        WHERE v.couplet_index = 1
    """)
    rows = cur.fetchall()
    patterns = []
    pattern_examples = {}
    for row in rows:
        text_id = row['id']
        misra = row['misra1_urdu']
        if not misra:
            continue
        _, _, pattern = detect_meter([{"misra1_urdu": misra}])
        if not pattern:
            continue
        patterns.append(pattern)
        if pattern not in pattern_examples:
            pattern_examples[pattern] = text_id
    counter = Counter(patterns)
    # Clear old data
    cur.execute("TRUNCATE TABLE meter_patterns RESTART IDENTITY")
    for pattern, freq in counter.items():
        cur.execute("""
            INSERT INTO meter_patterns (pattern, frequency, example_text_id)
            VALUES (%s, %s, %s)
        """, (pattern, freq, pattern_examples.get(pattern)))
    conn.commit()
    cur.close()
    conn.close()
    print(f"✅ Meter patterns learned: {len(counter)} unique patterns.")

if __name__ == "__main__":
    main()