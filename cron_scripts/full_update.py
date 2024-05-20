import requests
from bs4 import BeautifulSoup
import time
import re
import psycopg2
from psycopg2 import pool
import datetime
import os
import sys
from urllib.parse import urlparse
from dotenv import load_dotenv

load_dotenv()

script_dir = os.path.abspath(os.path.dirname(__file__))
root_dir = os.path.abspath(os.path.join(script_dir, '..'))
sys.path.append(root_dir)

COOKIE = os.getenv('COOKIE')
USER_AGENT = os.getenv('USER_AGENT')
HOST = os.getenv('HOST')
SITEMAP_URLS = os.getenv('SITEMAP_URLS', '').split(',')

DATABASE_URL = os.getenv('DATABASE_URL')

result = urlparse(DATABASE_URL)
username = result.username
password = result.password
database = result.path[1:]
hostname = result.hostname
port = result.port

IMAGE_DIR = os.path.join(root_dir, 'static', 'images')

start = time.time()

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

def parse_date(date_str):
    return datetime.datetime.strptime(date_str, "%d.%m.%Y")

def sixty_days_ago():
    return datetime.datetime.now() - datetime.timedelta(days=60)

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
conn.commit()
release_db_connection(conn)

for sitemap_url in SITEMAP_URLS:
    print(f"Checking {sitemap_url}")
    response = requests.get(sitemap_url)
    sitemap_soup = BeautifulSoup(response.content, 'xml')

    urls = [loc.text for loc in sitemap_soup.find_all('loc')]

    for url in urls:
        try:
            headers = {
                'Cookie': f'{COOKIE}',
                'Host': f'{HOST}',
                'User-Agent': f'{USER_AGENT}',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
                'Accept-Language': 'lv,en-US;q=0.7,en;q=0.3',
                'Accept-Encoding': 'gzip, deflate, zstd',
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

            sku_info = soup.find('form', class_='cart').get_text()

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

            conn = get_db_connection()
            c = conn.cursor()

            c.execute('SELECT version FROM products WHERE url = %s', (url,))
            existing_version = c.fetchone()

            if existing_version is None:
                c.execute('''
                    INSERT INTO products (name, url, category, download_link, image_url, version, last_updated, sku_external, id_external)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ''', (product_name, url, category, download_link, image_url, product_version, last_updated, sku, id_external))
                print(f"Added to database: {product_name}")
            elif existing_version[0] != product_version:
                c.execute('''
                    UPDATE products
                    SET name = %s, category = %s, download_link = %s, image_url = %s, version = %s, last_updated = %s, sku_external = %s, id_external = %s
                    WHERE url = %s
                ''', (product_name, category, download_link, image_url, product_version, last_updated, sku, id_external, url))
                print(f"Updated in database: {product_name}. Previous version {existing_version[0]}. New version {product_version}.")
            else:
                print(f"No changes for {product_name}, skipping update.")

            conn.commit()
            release_db_connection(conn)

        except Exception as e:
            print(f"Failed to process URL {url}: {e}")
            continue

end = time.time()
total = end - start
print(f'It took {total} seconds to complete the operation.')

connection_pool.closeall()