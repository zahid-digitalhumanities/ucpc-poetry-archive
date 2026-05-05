# scripts/populate_radif_qaafiya.py
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.base import get_db_connection
from modules.radif_qaafiya import process_ghazal

def ensure_poetic_features_table(conn):
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS poetic_features (
            id SERIAL PRIMARY KEY,
            text_id INTEGER UNIQUE REFERENCES texts(id) ON DELETE CASCADE,
            radif TEXT,
            qaafiya TEXT[],
            confidence FLOAT,
            meter TEXT,
            theme TEXT,
            created_at TIMESTAMP DEFAULT NOW()
        )
    """)
    # Add columns if they don't exist (idempotent)
    for col in ["meter", "theme"]:
        cur.execute(f"""
            DO $$
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                               WHERE table_name='poetic_features' AND column_name='{col}') THEN
                    ALTER TABLE poetic_features ADD COLUMN {col} TEXT;
                END IF;
            END
            $$;
        """)
    conn.commit()
    cur.close()

def populate():
    conn = get_db_connection()
    ensure_poetic_features_table(conn)

    cur = conn.cursor()
    cur.execute("SELECT id, text_urdu FROM texts WHERE text_urdu IS NOT NULL")
    rows = cur.fetchall()
    total = len(rows)
    print(f"Processing {total} ghazals...")

    updated = 0
    for i, row in enumerate(rows):
        text_id = row['id']
        text = row['text_urdu']
        result = process_ghazal(text_id, text)

        cur.execute("""
            INSERT INTO poetic_features (text_id, radif, qaafiya, confidence, meter, theme)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (text_id) DO UPDATE SET
                radif = EXCLUDED.radif,
                qaafiya = EXCLUDED.qaafiya,
                confidence = EXCLUDED.confidence,
                meter = EXCLUDED.meter,
                theme = EXCLUDED.theme,
                created_at = NOW()
        """, (
            text_id,
            result['radif'],
            result['qaafiya'],
            result['confidence'],
            result['meter'],
            result['theme']
        ))
        updated += 1
        if (i+1) % 100 == 0:
            conn.commit()
            print(f"Processed {i+1}/{total}")

    conn.commit()
    cur.close()
    conn.close()
    print(f"✅ Done. Updated {updated} ghazals.")

if __name__ == "__main__":
    populate()