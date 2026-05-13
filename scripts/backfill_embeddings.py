import sys
import os
import traceback

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.base import get_db_connection
from modules.embeddings import update_ghazal_embedding

def backfill_embeddings():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT t.id
        FROM texts t
        LEFT JOIN ghazal_embeddings g ON t.id = g.text_id
        WHERE t.is_deleted = FALSE
          AND g.text_id IS NULL
        ORDER BY t.id
    """)
    rows = cur.fetchall()
    total = len(rows)
    print(f"\n==================================================")
    print(f" FOUND {total} TEXTS WITHOUT EMBEDDINGS")
    print("==================================================\n")
    success = 0
    failed = 0
    for idx, row in enumerate(rows, 1):
        text_id = row['id']
        try:
            update_ghazal_embedding(text_id)
            cur.execute("UPDATE texts SET embedding_generated = TRUE WHERE id = %s", (text_id,))
            conn.commit()
            success += 1
            print(f"✅ [{idx}/{total}] Embedded text {text_id}")
        except Exception as e:
            conn.rollback()
            failed += 1
            print(f"\n❌ Error on text {text_id}:")
            print(str(e))
            traceback.print_exc()
            print("-" * 60)
    cur.close()
    conn.close()
    print("\n==================================================")
    print(" EMBEDDING BACKFILL COMPLETE")
    print("==================================================")
    print(f"✔ Success : {success}")
    print(f"❌ Failed  : {failed}")
    print(f"📚 Total   : {total}")
    print("==================================================")

if __name__ == "__main__":
    backfill_embeddings()