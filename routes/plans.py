from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
import stripe
from lib.database import get_db_connection
import datetime

plans_bp = Blueprint('plans', __name__)

plans = {
    1: {'price': 1000, 'description': "Pamata Plāns - 10 EUR mēnesī"},
    2: {'price': 2500, 'description': "Premium Plāns - 25 EUR mēnesī"}
}

@plans_bp.route('/plans')
def show_plans():
    return render_template('plans.html')

@plans_bp.route('/plan/<int:plan_id>')
@login_required
def process_payment(plan_id):
    if plan_id not in plans:
        flash('Tāda plāna pagaidām vēl nav!', 'error')
        return redirect(url_for('index.index'))

    if current_user.sub_level in [1, 2]:
        plan_name = plans[current_user.sub_level]['description'].split(" - ")[0] 
        flash(f'Tev jau ir aktīvs {plan_name}!<br>Ja vēlies to mainīt, <b><a href="{url_for('contacts.contacts')}">sazinies ar mums!</a></b>', 'info')
        return redirect(url_for('index.index'))

    plan = plans[plan_id]
    try:
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'eur',
                    'product_data': {
                        'name': plan['description'],
                    },
                    'unit_amount': plan['price'],
                },
                'quantity': 1,
            }],
            mode='payment',
            metadata={'plan_id': plan_id},
            success_url=url_for('plans.success', _external=True) + '?session_id={CHECKOUT_SESSION_ID}',
            cancel_url=url_for('plans.cancel', _external=True),
        )
        return redirect(session.url, code=303)
    except Exception as e:
        flash(str(e), 'error')
        return redirect(url_for('index.index')), 403


@plans_bp.route('/success')
def success():
    session_id = request.args.get('session_id')
    session = stripe.checkout.Session.retrieve(session_id)

    try:
        customer_email = session['customer_details']['email']
    except KeyError:
        customer_email = None
    
    try:
        customer_name = session['customer_details']['name']
    except KeyError:
        customer_name = None
    
    try:
        conn = get_db_connection()
        c = conn.cursor()
        new_sub_date = (datetime.datetime.now() + datetime.timedelta(days=30)).strftime('%d-%m-%Y')

        c.execute('''
            UPDATE users
            SET downloads_remaining = 5, sub_date = ?, sub_level = ?
            WHERE id = ?
        ''', (new_sub_date, session.metadata['plan_id'], current_user.id))

        c.execute('''
            INSERT INTO purchases (user_id, plan_id, billing_name, billing_email)
            VALUES (?, ?, ?, ?)
        ''', (current_user.id, session.metadata['plan_id'], customer_name, customer_email))

        conn.commit()

        flash('Pirkums veiksmīgi veikts, liels paldies par abonēšanu! Veiksmīgu Wordpressingu 😎', 'success')
    except Exception as e:
        flash('Kļūda iegādājoties abonementu', 'error')
        return redirect(url_for('index.index')), 500
    finally:
        conn.close()

    return redirect(url_for('index.index'))


@plans_bp.route('/cancel')
def cancel():
    flash('Maksājums neizdevās! Mēģini vēlreiz!', 'error')
    return redirect(url_for('plans.show_plans'))