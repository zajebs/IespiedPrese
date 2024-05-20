from flask_login import LoginManager
from lib.models import User
from lib.database import get_db_connection

login_manager = LoginManager()

@login_manager.user_loader
def load_user(user_id):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('SELECT * FROM users WHERE id = ?', (user_id,))
    user = c.fetchone()
    conn.close()
    if user:
        return User(user['id'], user['username'], user['email'], user['downloads_remaining'], user['sub_date'], user['sub_level'])
    return None

def init_login_manager(app):
    login_manager.login_message = 'Lūdzu, pieslēdzies, lai piekļūtu šim!'
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
