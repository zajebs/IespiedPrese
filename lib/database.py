import os
import psycopg2
from urllib.parse import urlparse
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv('DATABASE_URL')

result = urlparse(DATABASE_URL)
username = result.username
password = result.password
database = result.path[1:]
hostname = result.hostname
port = result.port

def get_db_connection():
    conn = psycopg2.connect(
        dbname=database,
        user=username,
        password=password,
        host=hostname,
        port=port
    )
    return conn

def setup_database():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id SERIAL PRIMARY KEY,
            name TEXT,
            url TEXT UNIQUE,
            category TEXT,
            download_link TEXT,
            image_url TEXT,
            version TEXT,
            last_updated TEXT,
            sku_external TEXT,
            id_external TEXT,
            downloads INTEGER NOT NULL DEFAULT 0
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            downloads_remaining INTEGER DEFAULT 0,
            sub_date TEXT DEFAULT NULL,
            sub_level INTEGER DEFAULT 0
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS promo (
            id SERIAL PRIMARY KEY,
            code TEXT UNIQUE NOT NULL,
            used_date TEXT DEFAULT NULL,
            used_by INTEGER DEFAULT NULL,
            FOREIGN KEY (used_by) REFERENCES users (id)
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS purchases (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL,
            utc_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            plan_id INTEGER NOT NULL,
            billing_name TEXT,
            billing_email TEXT,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS downloads (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            version TEXT,
            promo_code TEXT DEFAULT NULL,
            utc_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (product_id) REFERENCES products (id),
            FOREIGN KEY (promo_code) REFERENCES promo (code)
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS activity (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL,
            ip_address TEXT,
            type TEXT,
            utc_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')

    conn.commit()
    conn.close()

setup_database()