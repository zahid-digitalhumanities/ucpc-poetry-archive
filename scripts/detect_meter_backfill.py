import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.base import get_db_connection
from models.bulk_model import analyze_ghazal

def main():
    # Get list of all text ids that are already processed (nlp_processed = True)
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id FROM texts WHERE nlp_processed IS TRUE")
    ids = [r['id'] for r in cur.fetchall()]
    cur.close()
    conn.close()  # close after fetching ids

    total = len(ids)
    for i, tid in enumerate(ids, 1):
        print(f"{i}/{total} → Running meter detection for ghazal {tid}")
        # Open a new connection for each ghazal to avoid stale connections
        conn = get_db_connection()
        analyze_ghazal(conn, tid)
        conn.close()  # close after analysis
    print("✅ Meter detection backfill complete.")

if __name__ == "__main__":
    main()