from flask import Blueprint, render_template, redirect, url_for, flash

contacts_bp = Blueprint('contacts', __name__)

@contacts_bp.route('/contacts')
def contacts():
    return render_template('contacts.html')

@contacts_bp.route('/forgot')
def forgot_password():
    flash('Sazinies ar mums, lai atjaunotu paroli!', 'info')
    return redirect(url_for('contacts.contacts'))
