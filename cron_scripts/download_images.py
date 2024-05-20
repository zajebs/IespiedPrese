import psycopg2
from psycopg2 import pool
import requests
from urllib.parse import urlparse
import os
import logging
import datetime
from dotenv import load_dotenv

load_dotenv()

script_dir = os.path.abspath(os.path.dirname(__file__))
root_dir = os.path.join(script_dir, '..')

DATABASE_URL = os.getenv('DATABASE_URL')

result = urlparse(DATABASE_URL)
username = result.username
password = result.password
database = result.path[1:]
hostname = result.hostname
port = result.port

IMAGE_DIR = os.path.join(root_dir, 'static', 'images')

log_dir = os.path.join(root_dir, 'logs')
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

log_filename = datetime.datetime.now().strftime(f'{log_dir}/%d_%m_%Y_image_downloads.log')
logging.basicConfig(level=logging.INFO, filename=log_filename, filemode='a',
                    format='%(asctime)s - %(levelname)s - %(message)s')

connection_pool = psycopg2.pool.SimpleConnectionPool(
    1,
    10,
    user=username,
    password=password,
    host=hostname,
    port=port,
    database=database
)

def get_db_connection():
    return connection_pool.getconn()

def release_db_connection(conn):
    connection_pool.putconn(conn)

def download_images():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT image_url FROM products')
    images = cur.fetchall()
    release_db_connection(conn)

    if not os.path.exists(IMAGE_DIR):
        os.makedirs(IMAGE_DIR)

    for image in images:
        image_url = image[0]
        if image_url:
            filename = os.path.basename(urlparse(image_url).path)
            file_path = os.path.join(IMAGE_DIR, filename)

            if not os.path.isfile(file_path):
                try:
                    response = requests.get(image_url, stream=True)
                    if response.status_code == 200:
                        with open(file_path, 'wb') as f:
                            for chunk in response.iter_content(1024):
                                f.write(chunk)
                        logging.info(f'Downloaded {filename}')
                    else:
                        logging.error(f'Failed to download {filename}. HTTP status code: {response.status_code}')
                except Exception as e:
                    logging.error(f'Failed to download {filename}. Error: {str(e)}')
            else:
                logging.info(f'File {filename} already exists.')

if __name__ == '__main__':
    download_images()
    connection_pool.closeall()