import os
import logging
import sys
from flask import Flask
from flask_bcrypt import Bcrypt
from flask_htmlmin import HTMLMIN
from lib.config import SECRET_KEY
from lib.login_manager import init_login_manager
from lib.blueprints import register_blueprints
from lib.helpers import str_to_bool
from dotenv import load_dotenv

class LoggerWriter:
    def __init__(self, level):
        self.level = level
    
    def write(self, message):
        if message and not message.isspace():
            self.level(message.strip())
    
    def flush(self):
        pass

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

stdout_handler = logging.StreamHandler(sys.stdout)
stdout_handler.setLevel(logging.DEBUG)
stdout_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))

logger.addHandler(stdout_handler)

sys.stdout = LoggerWriter(logger.info)
sys.stderr = LoggerWriter(logger.error)

load_dotenv()
PORT = os.getenv('PORT')
DEBUG = str_to_bool(os.getenv('DEBUG', 'False'))
print(DEBUG)

def create_app():
    app = Flask(__name__)
    app.secret_key = SECRET_KEY
    app.config['MINIFY_HTML'] = True
    HTMLMIN(app)
    Bcrypt(app)
    init_login_manager(app)
    register_blueprints(app)
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=PORT, debug=DEBUG)
