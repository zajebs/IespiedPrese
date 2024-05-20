from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from lib.helpers import parse_version, format_promo_code, validate_email
from lib.database import get_db_connection
from flask_bcrypt import Bcrypt
import datetime
import sqlite3

bcrypt = Bcrypt()
account_bp = Blueprint('account', __name__)

@account_bp.route('/account', methods=['GET', 'POST'])
@login_required
def account():
    page = request.args.get('page', 1, type=int)
    per_page = 5
    offset = (page - 1) * per_page

    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute('''
            SELECT downloads.id, products.name as product_name, downloads.version as downloaded_version, downloads.promo_code, downloads.utc_date, products.version as current_version
            FROM downloads
            JOIN products ON downloads.product_id = products.id
            WHERE downloads.user_id = ?
            ORDER BY downloads.utc_date DESC
        ''', (current_user.id,))
        all_downloads = cur.fetchall()
        
        latest_versions = {}
        processed_downloads = []

        for row in all_downloads:
            product_name = row['product_name']
            downloaded_version = row['downloaded_version']
            
            if (product_name not in latest_versions or 
                parse_version(downloaded_version) > parse_version(latest_versions[product_name])):
                latest_versions[product_name] = downloaded_version

        for row in all_downloads[offset:offset + per_page]:
            product_name = row['product_name']
            downloaded_version = row['downloaded_version']
            current_version = row['current_version']
            
            is_latest = (downloaded_version == latest_versions[product_name])
            button_label = 'Lejuplādēt'
            
            if is_latest and parse_version(downloaded_version) < parse_version(current_version):
                button_label = 'Atjaunināt'

            processed_downloads.append({
                'product_name': product_name,
                'utc_date': datetime.datetime.strptime(row['utc_date'], '%Y-%m-%d %H:%M:%S').strftime('%d.%m.%Y'),
                'downloaded_version': downloaded_version,
                'current_version': current_version,
                'promo_code': format_promo_code(row['promo_code']) if row['promo_code'] else '',
                'button_label': button_label,
                'update_url': url_for('index.index') + f'?update={product_name}'
            })
        
        total_downloads = len(all_downloads)
        total_pages = (total_downloads + per_page - 1) // per_page

        cur.execute('''
            SELECT utc_date, plan_id, billing_name, billing_email
            FROM purchases
            WHERE user_id = ?
            ORDER BY utc_date DESC
        ''', (current_user.id,))
        purchases = cur.fetchall()
        subscription_history = [{
            'utc_date': datetime.datetime.strptime(row['utc_date'], '%Y-%m-%d %H:%M:%S').strftime('%d.%m.%Y'),
            'plan_name': 'Pamata plāns' if row['plan_id'] == 1 else 'Premium plāns',
            'billing_name': row['billing_name'],
            'billing_email': row['billing_email']
        } for row in purchases]

    finally:
        conn.close()

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return render_template('downloads_table.html', downloads=processed_downloads, total_pages=total_pages, current_page=page, subscription_history=subscription_history)

    return render_template('account.html', downloads=processed_downloads, total_pages=total_pages, current_page=page, subscription_history=subscription_history, email=current_user.email)

@account_bp.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    if request.method == 'POST':
        current_password = request.form['current_password']
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']

        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE id = ?', (current_user.id,)).fetchone()
        conn.close()

        if not bcrypt.check_password_hash(user['password_hash'], current_password):
            flash('Nepareiza pašreizējā parole!', 'error')
            return redirect(url_for('account.change_password'))

        if new_password != confirm_password:
            flash('Jaunā parole un apstiprinājums nesakrīt!', 'error')
            return redirect(url_for('account.change_password'))

        if len(new_password) < 8:
            flash('Parolei jābūt vismaz 8 simbolu garai!', 'error')
            return redirect(url_for('account.change_password'))

        hashed_password = bcrypt.generate_password_hash(new_password).decode('utf-8')
        conn = get_db_connection()
        conn.execute('UPDATE users SET password_hash = ? WHERE id = ?', (hashed_password, current_user.id))
        conn.commit()
        conn.close()

        flash('Parole veiksmīgi nomainīta!', 'success')
        return redirect(url_for('account.account'))

    return render_template('change_password.html')

@account_bp.route('/change_email', methods=['GET', 'POST'])
@login_required
def change_email():
    if request.method == 'POST':
        current_password = request.form['current_password']
        new_email = request.form['new_email']
        confirm_email = request.form['confirm_email']

        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE id = ?', (current_user.id,)).fetchone()
        conn.close()

        if not bcrypt.check_password_hash(user['password_hash'], current_password):
            flash('Nepareiza pašreizējā parole!', 'error')
            return redirect(url_for('account.change_email'))

        if new_email != confirm_email:
            flash('Jaunais e-pasts un apstiprinājums nesakrīt!', 'error')
            return redirect(url_for('account.change_email'))

        if not validate_email(new_email):
            flash('Nederīgs e-pasta formāts!', 'error')
            return redirect(url_for('account.change_email'))

        conn = get_db_connection()
        try:
            conn.execute('UPDATE users SET email = ? WHERE id = ?', (new_email, current_user.id))
            conn.commit()
        except sqlite3.IntegrityError:
            flash('E-pasta adrese jau ir aizņemta!', 'error')
            return redirect(url_for('account.change_email'))
        finally:
            conn.close()

        flash(f'E-pasts veiksmīgi nomainīts uz <b>{new_email}</b>!', 'success')
        return redirect(url_for('account.account'))

    return render_template('change_email.html')