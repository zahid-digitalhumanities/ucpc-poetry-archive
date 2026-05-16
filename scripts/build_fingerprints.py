import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.base import get_db_connection
from modules.fingerprint import build_poet_fingerprint

def main():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id FROM poets")
    poets = [r['id'] for r in cur.fetchall()]
    cur.close()
    conn.close()

    for p in poets:
        print(f"Building fingerprint for poet {p}")
        build_poet_fingerprint(p)

    print("✅ All poet fingerprints built.")

if __name__ == "__main__":
    main()