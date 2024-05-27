import os
from flask import Flask, send_from_directory, request
from flask_bcrypt import Bcrypt
from flask_htmlmin import HTMLMIN
from lib.config import SECRET_KEY
from lib.login_manager import init_login_manager
from lib.blueprints import register_blueprints
from lib.helpers import str_to_bool
from dotenv import load_dotenv
from flask_squeeze import Squeeze
from datetime import datetime, timedelta

squeeze = Squeeze()
load_dotenv()
PORT = int(os.getenv('PORT'))
DEBUG = str_to_bool(os.getenv('DEBUG', 'False'))
CACHE_AGE = int(os.getenv('CACHE_AGE'))
GA_MEASUREMENT_ID = (os.getenv('GA_MEASUREMENT_ID'))

def create_app():
    app = Flask(__name__)
    squeeze.init_app(app)
    app.secret_key = SECRET_KEY
    app.config['MINIFY_HTML'] = True
    HTMLMIN(app)
    Bcrypt(app)
    init_login_manager(app)
    register_blueprints(app)

    @app.context_processor
    def inject_ga_measurement_id():
        return dict(GA_MEASUREMENT_ID=GA_MEASUREMENT_ID)

    @app.after_request
    def add_header(response):
        if request.path.startswith('/static/'):
            expires = datetime.utcnow() + timedelta(days=CACHE_AGE)
            response.headers['Expires'] = expires.strftime("%a, %d %b %Y %H:%M:%S GMT")
            response.headers['Cache-Control'] = f'public, max-age={CACHE_AGE*60*60*24}'
        return response

    @app.route('/static/<path:filename>')
    def custom_static(filename):
        response = send_from_directory(app.static_folder, filename)
        expires = datetime.utcnow() + timedelta(days=CACHE_AGE)
        response.headers['Expires'] = expires.strftime("%a, %d %b %Y %H:%M:%S GMT")
        response.headers['Cache-Control'] = f'public, max-age={CACHE_AGE*60*60*24}'
        return response
    
    @app.route('/robots.txt')
    def robots_txt():
        return send_from_directory(app.static_folder, 'robots.txt')

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=PORT, debug=DEBUG)