import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
from flask import Flask, send_from_directory, request, redirect
from flask_bcrypt import Bcrypt
from flask_htmlmin import HTMLMIN
from flask_squeeze import Squeeze
from flask_talisman import Talisman
from lib.config import SECRET_KEY
from lib.login_manager import init_login_manager
from lib.blueprints import register_blueprints
from lib.helpers import str_to_bool

squeeze = Squeeze()
load_dotenv()
PORT = int(os.getenv('PORT'))
DEBUG = str_to_bool(os.getenv('DEBUG', 'False'))
CACHE_AGE = int(os.getenv('CACHE_AGE'))
GA_MEASUREMENT_ID = os.getenv('GA_MEASUREMENT_ID')
SPECIFIC_PATH = os.getenv('SPECIFIC_PATH')
SSL_ENABLED = str_to_bool(os.getenv('SSL_ENABLED', 'True'))

def create_app():
    app = Flask(__name__)
    squeeze.init_app(app)
    app.secret_key = SECRET_KEY
    app.config['MINIFY_HTML'] = True
    HTMLMIN(app)
    Bcrypt(app)
    init_login_manager(app)
    register_blueprints(app)
    
    if SSL_ENABLED:
        Talisman(app)
    
    @app.before_request
    def before_request():
        if not request.is_secure and SSL_ENABLED:
            url = request.url.replace("http://", "https://", 1)
            return redirect(url, code=301)

    @app.context_processor
    def inject_ga_measurement_id():
        return dict(GA_MEASUREMENT_ID=GA_MEASUREMENT_ID, SPECIFIC_PATH=SPECIFIC_PATH)

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