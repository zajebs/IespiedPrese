import requests
from bs4 import BeautifulSoup
import time
import re
import sqlite3
import logging
import datetime
import os
import sys
from dotenv import load_dotenv

load_dotenv()

script_dir = os.path.abspath(os.path.dirname(__file__))
root_dir = os.path.abspath(os.path.join(script_dir, '..'))
sys.path.append(root_dir)

COOKIE = os.getenv('COOKIE')
USER_AGENT = os.getenv('USER_AGENT')
HOST = os.getenv('HOST')
SITEMAP_URLS = os.getenv('SITEMAP_URLS', '').split(',')

DB_PATH = os.path.join(root_dir, 'database.db')
log_dir = os.path.join(root_dir, 'logs')

if not os.path.exists(log_dir):
    os.makedirs(log_dir)

log_filename = datetime.datetime.now().strftime(f'{log_dir}/%d_%m_%Y_product_updates.log')
logging.basicConfig(level=logging.INFO, filename=log_filename, filemode='a',
                    format='%(asctime)s - %(levelname)s - %(message)s')

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)
logging.getLogger().addHandler(console_handler)

start = time.time()

conn = sqlite3.connect(DB_PATH)
c = conn.cursor()
c.execute('''
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
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
conn.commit()

def parse_date(date_str):
    return datetime.datetime.strptime(date_str, "%d.%m.%Y")

def sixty_days_ago():
    return datetime.datetime.now() - datetime.timedelta(days=60)

for sitemap_url in SITEMAP_URLS:
    logging.info(f"Checking {sitemap_url}")
    response = requests.get(sitemap_url)
    sitemap_soup = BeautifulSoup(response.content, 'xml')

    urls = [loc.text for loc in sitemap_soup.find_all('loc')]

    for url in urls:

        c.execute('SELECT id FROM products WHERE url = ?', (url,))
        if c.fetchone():
            logging.info(f"Product already in database: {url}")
            continue 

        try:
            headers = {
                'Cookie': COOKIE,
                'Host': f'{HOST}',
                'User-Agent': USER_AGENT,
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate, br, zstd',
                'Alt-Used': f'{HOST}',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1',
                'Priority': 'u=1',
                'Pragma': 'no-cache',
                'Cache-Control': 'no-cache',
                'TE': 'trailers'
            }

            response = requests.get(url, headers=headers)
            soup = BeautifulSoup(response.text, 'html.parser')

            try:
                download_link = soup.find('a', class_='red-link')['href']
            except:
                continue

            image_url = soup.find('img', class_='wp-post-image')['src']

            product_name = soup.find('h1', class_='product-title').text.strip()

            product_info = soup.find('div', class_='product-short-description').get_text()

            version_match = re.search(r'Product Version :\s*(.*)', product_info)
            product_version = version_match.group(1).strip() if version_match else "Produkta versija nav atrasta"

            update_match = re.search(r'Product Last Updated :\s*(.*)', product_info)
            if update_match:
                last_updated = update_match.group(1).strip()
            else:
                last_updated = sixty_days_ago().strftime("%d.%m.%Y")

            if "License" in last_updated:
                last_updated = (datetime.datetime.now() - datetime.timedelta(days=60)).strftime("%d.%m.%Y")
            else:
                try:
                    last_updated_date = parse_date(last_updated)
                    if last_updated_date > datetime.datetime.now():
                        last_updated = sixty_days_ago().strftime("%d.%m.%Y")
                    else:
                        last_updated = last_updated_date.strftime("%d.%m.%Y")
                except ValueError:
                    last_updated = sixty_days_ago().strftime("%d.%m.%Y")

            sku_input = soup.find('input', {'name': 'gtm4wp_sku'})
            sku = sku_input['value'] if sku_input else "SKU not found"

            category_input = soup.find('input', {'name': 'gtm4wp_category'})
            category = category_input['value'] if category_input else "Category not found"

            id_input = soup.find('input', {'name': 'gtm4wp_id'})
            id_external = id_input['value'] if id_input else "ID not found"

            c.execute('''
                INSERT INTO products (name, url, category, download_link, image_url, version, last_updated, sku_external, id_external)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (product_name, url, category, download_link, image_url, product_version, last_updated, sku, id_external))
            conn.commit()

            logging.info(f"Added to database: {product_name}")
        
        except Exception as e:
            logging.error(f"Failed to process URL {url}: {e}")
            continue

end = time.time()
total = end - start
logging.info(f'It took {total} seconds to complete the operation.')

conn.close()
