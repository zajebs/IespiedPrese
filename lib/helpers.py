import os
import re
import time
import threading
import shutil
import requests
import uuid
import datetime
from dotenv import load_dotenv
from urllib.parse import urlparse
from flask_login import current_user
from .config import TEMP_DIR
from .database import get_db_connection

load_dotenv()

AWS_BUCKET_NAME = os.getenv('BUCKETEER_BUCKET_NAME')
AWS_REGION = os.getenv('BUCKETEER_AWS_REGION')

def convert_external_url_to_amazon(image_url):
    if not image_url:
        return None
    filename = os.path.basename(urlparse(image_url).path)
    filename_webp = f"{os.path.splitext(filename)[0]}.webp"
    return f"https://{AWS_BUCKET_NAME}.s3.{AWS_REGION}.amazonaws.com/public/{filename_webp}"

def str_to_bool(s):
    return s.lower() in ('true', '1', 't', 'y', 'yes')

def download_file(product):
    url = product[4]
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
    cur = conn.cursor()
    cur.execute('UPDATE products SET downloads = downloads + 1 WHERE id = %s', (product_id,))
    conn.commit()
    cur.close()
    conn.close()

def mark_promo_code_used(promo_id):
    conn = get_db_connection()
    cur = conn.cursor()
    current_time = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=3)
    cur.execute('UPDATE promo SET used_date = %s, used_by = %s WHERE id = %s', 
                (current_time, current_user.id, promo_id))
    conn.commit()
    cur.close()
    conn.close()

def insert_download(user_id, product_id, version, promo_code=None):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('''
        INSERT INTO downloads (user_id, product_id, version, promo_code)
        VALUES (%s, %s, %s, %s)
        ''', (user_id, product_id, version, promo_code))
    conn.commit()
    cur.close()
    conn.close()

def decrement_user_downloads():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('UPDATE users SET downloads_remaining = downloads_remaining - 1 WHERE id = %s', (current_user.id,))
    conn.commit()
    cur.close()
    conn.close()

def log_activity(user_id, ip_address, activity_type):
    conn = get_db_connection()
    c = conn.cursor()
    try:
        c.execute('''
            INSERT INTO activity (user_id, ip_address, type, utc_date)
            VALUES (%s, %s, %s, %s)
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

def fetch_all_downloads_for_user(user_id):
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute('''
            SELECT downloads.id, products.name as product_name, downloads.version as downloaded_version, products.version as current_version
            FROM downloads
            JOIN products ON downloads.product_id = products.id
            WHERE downloads.user_id = %s
            ORDER BY downloads.utc_date DESC
        ''', (user_id,))
        return cur.fetchall()
    finally:
        cur.close()
        conn.close()

def get_latest_versions(all_downloads):
    latest_versions = {}
    for row in all_downloads:
        product_name = row[1]
        downloaded_version = row[2]
        if product_name not in latest_versions or parse_version(downloaded_version) > parse_version(latest_versions[product_name]):
            latest_versions[product_name] = downloaded_version
    return latest_versions

def count_updatable_products(all_downloads, latest_versions):
    updatable_count = 0
    for row in all_downloads:
        product_name = row[1]
        downloaded_version = row[2]
        current_version = row[3]
        if (downloaded_version == latest_versions[product_name]) and (parse_version(downloaded_version) < parse_version(current_version)):
            updatable_count += 1
    return updatable_count
