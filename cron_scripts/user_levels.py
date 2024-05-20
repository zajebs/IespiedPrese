import psycopg2
from psycopg2 import pool
import datetime
import logging
import os
from urllib.parse import urlparse
from dotenv import load_dotenv

load_dotenv()

script_dir = os.path.abspath(os.path.dirname(__file__))
root_dir = os.path.abspath(os.path.join(script_dir, '..'))

log_dir = os.path.join(root_dir, 'logs')
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

log_filename = datetime.datetime.now().strftime(f'{log_dir}/%d_%m_%Y_subscription_updates.log')
logging.basicConfig(level=logging.INFO, filename=log_filename, filemode='a',
                    format='%(asctime)s - %(levelname)s - %(message)s')

DATABASE_URL = os.getenv('DATABASE_URL')

result = urlparse(DATABASE_URL)
username = result.username
password = result.password
database = result.path[1:]
hostname = result.hostname
port = result.port

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

def get_yesterday_date():
    yesterday = datetime.datetime.now() - datetime.timedelta(days=1)
    return yesterday.strftime('%d-%m-%Y')

def update_expired_subscriptions():
    yesterday_date = get_yesterday_date()
    conn = get_db_connection()
    c = conn.cursor()
    
    try:
        c.execute('SELECT id, username, sub_date FROM users')
        users = c.fetchall()
        for user in users:
            sub_date_str = user[2]
            if sub_date_str:
                sub_date = datetime.datetime.strptime(sub_date_str, '%d-%m-%Y')
                days_diff = (sub_date - datetime.datetime.strptime(yesterday_date, '%d-%m-%Y')).days
                logging.info(f"User {user[1]} subscription days difference: {days_diff}")
        
        c.execute('''
            UPDATE users
            SET sub_level = 0
            WHERE sub_date = %s
        ''', (yesterday_date,))
        
        conn.commit()
        logging.info(f"Updated {c.rowcount} users whose subscription expired on {yesterday_date}.")
    except Exception as e:
        logging.error(f"Failed to update subscriptions: {str(e)}")
    finally:
        release_db_connection(conn)

if __name__ == '__main__':
    update_expired_subscriptions()
    connection_pool.closeall()
