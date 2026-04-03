import psycopg2
from config import DB_CONFIG

def get_db_connection():
    if 'dsn' in DB_CONFIG:
        return psycopg2.connect(DB_CONFIG['dsn'])
    return psycopg2.connect(**DB_CONFIG)