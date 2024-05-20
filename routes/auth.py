from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from lib.helpers import log_activity, validate_email
from lib.database import get_db_connection
from lib.models import User
from flask_bcrypt import Bcrypt
import sqlite3

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
        try:
            conn.execute('INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)',
                         (username, email, hashed_password))
            conn.commit()

            user_id = conn.execute('SELECT id FROM users WHERE username = ?', (username,)).fetchone()['id']
            user_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
            log_activity(user_id, user_ip, 'Register')

        except sqlite3.IntegrityError:
            flash('Lietotājvārds vai e-pasts jau ir aizņemts!', 'error')
            return render_template('register.html')
        finally:
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
        try:
            if '@' in login_input:
                user = conn.execute('SELECT id, username, email, password_hash, downloads_remaining, sub_date, sub_level FROM users WHERE email = ?', (login_input,)).fetchone()
            else:
                user = conn.execute('SELECT id, username, email, password_hash, downloads_remaining, sub_date, sub_level FROM users WHERE username = ?', (login_input,)).fetchone()
        finally:
            conn.close()

        if user and bcrypt.check_password_hash(user['password_hash'], password):
            user_obj = User(id=user['id'], username=user['username'], email=user['email'], downloads_remaining=user['downloads_remaining'], sub_date=user['sub_date'], sub_level=user['sub_level'])
            login_user(user_obj)
            user_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
            log_activity(user['id'], user_ip, 'Login')
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