import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.base import get_db_connection
from modules.embeddings import update_ghazal_embedding


def ensure_column_exists(conn):
    """
    Ensure embedding_generated column exists
    """
    cur = conn.cursor()
    cur.execute("""
        ALTER TABLE texts
        ADD COLUMN IF NOT EXISTS embedding_generated BOOLEAN DEFAULT FALSE
    """)
    conn.commit()
    cur.close()


def backfill_embeddings():
    conn = get_db_connection()
    ensure_column_exists(conn)

    cur = conn.cursor()

    # ✅ Correct query
    cur.execute("""
        SELECT id 
        FROM texts 
        WHERE (embedding_generated IS FALSE OR embedding_generated IS NULL)
        AND text_urdu IS NOT NULL
    """)

    rows = cur.fetchall()
    total = len(rows)

    print(f"🚀 Found {total} ghazals without embeddings.")

    success = 0
    failed = 0

    for i, row in enumerate(rows):
        text_id = row['id']   # ✅ FIXED

        try:
            update_ghazal_embedding(text_id)

            cur.execute("""
                UPDATE texts 
                SET embedding_generated = TRUE 
                WHERE id = %s
            """, (text_id,))

            success += 1

        except Exception as e:
            failed += 1
            print(f"❌ Error embedding {text_id}: {e}")

        # ✅ Batch commit every 50
        if (i + 1) % 50 == 0:
            conn.commit()
            print(f"⚡ Progress: {i+1}/{total} | Success: {success} | Failed: {failed}")

    conn.commit()
    cur.close()
    conn.close()

    print("\n✅ Embedding Backfill Complete")
    print(f"✔ Success: {success}")
    print(f"❌ Failed: {failed}")


if __name__ == "__main__":
    backfill_embeddings()