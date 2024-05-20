from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from lib.helpers import log_activity, validate_email
from lib.database import get_db_connection
from lib.models import User
from flask_bcrypt import Bcrypt
import psycopg2

auth_bp = Blueprint('auth', __name__)
bcrypt = Bcrypt()

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        if len(username) < 5:
            flash('Lietotājvārdam jābūt vismaz 5 simbolu garam!', 'error')
            return render_template('register.html')

        if len(password) < 8:
            flash('Parolei jābūt vismaz 8 simbolu garai!', 'error')
            return render_template('register.html')

        if not validate_email(email):
            flash('Nederīgs e-pasta formāts!', 'error')
            return render_template('register.html')

        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute('INSERT INTO users (username, email, password_hash) VALUES (%s, %s, %s)',
                        (username, email, hashed_password))
            conn.commit()

            cur.execute('SELECT id FROM users WHERE username = %s', (username,))
            user_id = cur.fetchone()[0]
            user_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
            log_activity(user_id, user_ip, 'Register')

        except psycopg2.IntegrityError:
            flash('Lietotājvārds vai e-pasts jau ir aizņemts!', 'error')
            return render_template('register.html')
        finally:
            cur.close()
            conn.close()

        flash(f'Paldies par reģistrāciju, {username}! Tagad vari pieslēgties.', 'success')
        return redirect(url_for('auth.login', user=username))
    return render_template('register.html')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    user_param = ''

    if request.method == 'POST':
        login_input = request.form['username']
        password = request.form['password']

        conn = get_db_connection()
        cur = conn.cursor()
        try:
            if '@' in login_input:
                cur.execute('SELECT id, username, email, password_hash, downloads_remaining, sub_date, sub_level FROM users WHERE email = %s', (login_input,))
            else:
                cur.execute('SELECT id, username, email, password_hash, downloads_remaining, sub_date, sub_level FROM users WHERE username = %s', (login_input,))
            user = cur.fetchone()
        finally:
            cur.close()
            conn.close()

        if user and bcrypt.check_password_hash(user[3], password):
            user_obj = User(id=user[0], username=user[1], email=user[2], downloads_remaining=user[4], sub_date=user[5], sub_level=user[6])
            login_user(user_obj)
            user_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
            log_activity(user[0], user_ip, 'Login')
            return redirect(url_for('index.index'))
        else:
            flash('Nepareizi dati!', 'error')
    
    if request.method == 'GET':
        user_param = request.args.get('user', '')
    
    return render_template('login.html', user=user_param)


@auth_bp.route('/logout')
@login_required
def logout():
    user_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    log_activity(current_user.id, user_ip, 'Logout')

    logout_user()
    return redirect(url_for('index.index'))