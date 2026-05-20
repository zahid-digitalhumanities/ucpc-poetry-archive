import os
import psycopg2                    # ← Fixed: psycopg2 (not pyscopq2)
from psycopg2.extras import RealDictCursor  # ← Fixed

DATABASE_URL = os.getenv("DATABASE_URL")

def get_db():
    return psycopg2.connect(        # ← Fixed
        DATABASE_URL,
        cursor_factory=RealDictCursor
    )
