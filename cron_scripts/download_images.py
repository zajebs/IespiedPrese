import sqlite3
import requests
from urllib.parse import urlparse
import os
import logging
import datetime

script_dir = os.path.abspath(os.path.dirname(__file__))
root_dir = os.path.join(script_dir, '..')

DB_PATH = os.path.join(root_dir, 'database.db')
IMAGE_DIR = os.path.join(root_dir, 'static', 'images')

log_dir = os.path.join(root_dir, 'logs')
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

log_filename = datetime.datetime.now().strftime(f'{log_dir}/%d_%m_%Y_image_downloads.log')
logging.basicConfig(level=logging.INFO, filename=log_filename, filemode='a',
                    format='%(asctime)s - %(levelname)s - %(message)s')

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def download_images():
    conn = get_db_connection()
    images = conn.execute('SELECT image_url FROM products').fetchall()
    conn.close()

    if not os.path.exists(IMAGE_DIR):
        os.makedirs(IMAGE_DIR)

    for image in images:
        image_url = image['image_url']
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
