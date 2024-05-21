import os
from flask import Flask
from flask_bcrypt import Bcrypt
from flask_htmlmin import HTMLMIN
from lib.config import SECRET_KEY
from lib.login_manager import init_login_manager
from lib.blueprints import register_blueprints
from lib.helpers import str_to_bool
from dotenv import load_dotenv
from flask_squeeze import Squeeze

squeeze = Squeeze()
load_dotenv()
PORT = os.getenv('PORT')
DEBUG = str_to_bool(os.getenv('DEBUG', 'False'))

def create_app():
    app = Flask(__name__)
    squeeze.init_app(app)
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
