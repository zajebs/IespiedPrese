import os
import stripe
from dotenv import load_dotenv

load_dotenv()

STRIPE_KEY = os.getenv('STRIPE_KEY')
SECRET_KEY = os.getenv('SECRET_KEY')

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
DB_PATH = os.path.join(BASE_DIR, 'database.db')
TEMP_DIR = os.path.join(BASE_DIR, 'temp')
os.makedirs(TEMP_DIR, exist_ok=True)

stripe.api_key = STRIPE_KEY
SECRET_KEY = SECRET_KEY
