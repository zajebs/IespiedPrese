import psycopg2
from psycopg2 import pool
import requests
from urllib.parse import urlparse
import os
import logging
import datetime
from dotenv import load_dotenv
import boto3
from botocore.exceptions import NoCredentialsError, ClientError

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

AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
AWS_REGION = os.getenv('AWS_REGION')
BUCKETEER_BUCKET_NAME = os.getenv('BUCKETEER_BUCKET_NAME')

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

s3 = boto3.client('s3',
                  aws_access_key_id=AWS_ACCESS_KEY_ID,
                  aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
                  region_name=AWS_REGION)

def get_db_connection():
    return connection_pool.getconn()

def release_db_connection(conn):
    connection_pool.putconn(conn)

def generate_s3_url(bucket_name, region, file_name):
    return f"https://{bucket_name}.s3.{region}.amazonaws.com/public/{file_name}"

def download_images():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT image_url FROM products')
    images = cur.fetchall()
    release_db_connection(conn)

    s3_urls = []

    for image in images:
        image_url = image[0]
        if image_url:
            print(image_url)
            filename = os.path.basename(urlparse(image_url).path)
            s3_key = f"public/{filename}"

            try:
                try:
                    s3.head_object(Bucket=BUCKETEER_BUCKET_NAME, Key=s3_key)
                    logging.info(f'File {filename} already exists in S3')
                    s3_url = generate_s3_url(BUCKETEER_BUCKET_NAME, AWS_REGION, filename)
                    s3_urls.append(s3_url)
                    continue
                except ClientError as e:
                    if e.response['Error']['Code'] == '404':
                        pass
                    else:
                        raise

                response = requests.get(image_url, stream=True)
                if response.status_code == 200:
                    s3.upload_fileobj(response.raw, BUCKETEER_BUCKET_NAME, s3_key)
                    s3_url = generate_s3_url(BUCKETEER_BUCKET_NAME, AWS_REGION, filename)
                    s3_urls.append(s3_url)
                    logging.info(f'Uploaded {filename} to S3')
                else:
                    logging.error(f'Failed to download {filename}. HTTP status code: {response.status_code}')
            except NoCredentialsError:
                logging.error('AWS credentials not available')
            except Exception as e:
                logging.error(f'Failed to download or upload {filename}. Error: {str(e)}')

if __name__ == '__main__':
    download_images()
    connection_pool.closeall()