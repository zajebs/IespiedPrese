import psycopg2
from psycopg2 import pool
import requests
from urllib.parse import urlparse
import os
from dotenv import load_dotenv
import boto3
from botocore.exceptions import NoCredentialsError, ClientError
from PIL import Image
from io import BytesIO
from datetime import datetime, timedelta, timezone

load_dotenv()

DATABASE_URL = os.getenv('DATABASE_URL')
CACHE_AGE = int(os.getenv('CACHE_AGE', '365'))

result = urlparse(DATABASE_URL)
username = result.username
password = result.password
database = result.path[1:]
hostname = result.hostname
port = result.port

AWS_ACCESS_KEY_ID = os.getenv('BUCKETEER_AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('BUCKETEER_AWS_SECRET_ACCESS_KEY')
AWS_REGION = os.getenv('BUCKETEER_AWS_REGION')
AWS_BUCKET_NAME = os.getenv('BUCKETEER_BUCKET_NAME')

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

def compress_image(image_data, target_size_kb, max_resolution=(256, 256)):
    img = Image.open(BytesIO(image_data))
    
    img.thumbnail(max_resolution, Image.LANCZOS)
    
    output = BytesIO()
    quality = 70

    while True:
        output.seek(0)
        img.save(output, format='WEBP', quality=quality)
        size_kb = output.tell() / 1024
        if size_kb <= target_size_kb:
            break
        quality -= 5
    
    while size_kb > target_size_kb and img.size[0] > 50 and img.size[1] > 50:
        new_width = max(img.size[0] // 2, 50)
        new_height = max(img.size[1] // 2, 50)
        img = img.resize((new_width, new_height), Image.LANCZOS)
        output = BytesIO()
        img.save(output, format='WEBP', quality=quality)
        size_kb = output.tell() / 1024
    
    return output

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
            print(f"Processing image: {image_url}")
            filename = os.path.basename(urlparse(image_url).path)
            filename_webp = f"{os.path.splitext(filename)[0]}.webp"
            s3_key = f"public/{filename_webp}"

            try:
                try:
                    s3.head_object(Bucket=AWS_BUCKET_NAME, Key=s3_key)
                    print(f'File {filename_webp} already exists in S3')
                    s3_url = generate_s3_url(AWS_BUCKET_NAME, AWS_REGION, filename_webp)
                    s3_urls.append(s3_url)
                    print(f"S3 URL: {s3_url}")
                    continue
                except ClientError as e:
                    if e.response['Error']['Code'] == '404':
                        pass
                    else:
                        raise

                response = requests.get(image_url, stream=True)
                if response.status_code == 200:
                    compressed_image = compress_image(response.content, 5)
                    compressed_image.seek(0)

                    cache_control = f'public, max-age={CACHE_AGE * 24 * 60 * 60}'
                    expires = (datetime.now(timezone.utc) + timedelta(days=CACHE_AGE)).strftime("%a, %d %b %Y %H:%M:%S GMT")

                    s3.upload_fileobj(compressed_image, AWS_BUCKET_NAME, s3_key,
                                      ExtraArgs={
                                          'CacheControl': cache_control,
                                          'Expires': expires
                                      })
                    s3_url = generate_s3_url(AWS_BUCKET_NAME, AWS_REGION, filename_webp)
                    s3_urls.append(s3_url)
                    print(f'Uploaded and compressed {filename_webp} to S3')
                    print(f"S3 URL: {s3_url}")
                else:
                    print(f'Failed to download {filename}. HTTP status code: {response.status_code}')
            except NoCredentialsError:
                print('AWS credentials not available')
            except Exception as e:
                print(f'Failed to download or upload {filename_webp}. Error: {str(e)}')

if __name__ == '__main__':
    download_images()
    connection_pool.closeall()
