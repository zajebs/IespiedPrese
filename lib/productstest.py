import sqlite3
import os

script_dir = os.path.abspath(os.path.dirname(__file__))
root_dir = os.path.abspath(os.path.join(script_dir, '..'))

def get_db_connection():
    DB_PATH = os.path.join(root_dir, 'database.db')
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

conn = get_db_connection()
c = conn.cursor()
c.execute('SELECT * FROM products')
rows = c.fetchall()
for row in rows:
    print(dict(row))
conn.close()