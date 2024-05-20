import os
import re
import time
import threading
import shutil
import requests
import uuid
import datetime
from urllib.parse import urlparse
from flask_login import current_user
from .config import TEMP_DIR
from .database import get_db_connection

def convert_external_url_to_internal(image_url):
    if not image_url:
        return None
    filename = os.path.basename(urlparse(image_url).path)
    return f"/static/images/{filename}"

def download_file(product):
    url = product['download_link']
    response = requests.get(url, stream=True)
    if response.status_code != 200:
        return None

    file_uuid = uuid.uuid4()
    original_filename = os.path.basename(url)
    new_filename = f"{os.path.splitext(original_filename)[0]}_{file_uuid}{os.path.splitext(original_filename)[1]}"

    temp_file_path = os.path.join(TEMP_DIR, new_filename)
    with open(temp_file_path, 'wb') as temp_file:
        shutil.copyfileobj(response.raw, temp_file)

    return temp_file_path, new_filename

def update_product_download_count(product_id):
    conn = get_db_connection()
    conn.execute('UPDATE products SET downloads = downloads + 1 WHERE id = ?', (product_id,))
    conn.commit()
    conn.close()

def mark_promo_code_used(promo_id):
    conn = get_db_connection()
    conn.execute('PRAGMA foreign_keys = ON')
    current_time = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=3)
    conn.execute('UPDATE promo SET used_date = ?, used_by = ? WHERE id = ?', 
                 (current_time, current_user.id, promo_id))
    conn.commit()
    conn.close()

def insert_download(user_id, product_id, version, promo_code):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('''
        INSERT INTO downloads (user_id, product_id, version, promo_code)
        VALUES (?, ?, ?, ?)
        ''', (user_id, product_id, version, promo_code))
    conn.commit()

def decrement_user_downloads():
    conn = get_db_connection()
    conn.execute('UPDATE users SET downloads_remaining = downloads_remaining - 1 WHERE id = ?', (current_user.id,))
    conn.commit()
    conn.close()

def log_activity(user_id, ip_address, activity_type):
    conn = get_db_connection()
    c = conn.cursor()
    try:
        c.execute('''
            INSERT INTO activity (user_id, ip_address, type, utc_date)
            VALUES (?, ?, ?, ?)
        ''', (user_id, ip_address, activity_type, datetime.datetime.utcnow()))
        conn.commit()
    finally:
        conn.close()

def parse_version(version):
    return tuple(map(int, re.findall(r'\d+', version)))

def format_promo_code(promo_code):
    if promo_code == 'PLAN1':
        return 'Pamata plāns'
    elif promo_code == 'PLAN2':
        return 'Premium plāns'
    return f"KODS: {promo_code}"

def validate_email(email):
    email_regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    return re.match(email_regex, email) is not None

def delayed_delete(file_path, delay=10):
    def attempt_delete():
        time.sleep(delay)
        try:
            os.unlink(file_path)
            print(f"Successfully deleted {file_path}")
        except Exception as e:
            print(f"Failed to delete {file_path}: {e}")

    thread = threading.Thread(target=attempt_delete)
    thread.start()
