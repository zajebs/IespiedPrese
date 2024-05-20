from flask import Blueprint, jsonify, send_file, flash, abort
from flask_login import login_required, current_user
from lib.helpers import (download_file, update_product_download_count, mark_promo_code_used, insert_download, 
                         decrement_user_downloads, delayed_delete)
from lib.database import get_db_connection
import datetime
import os

downloads_bp = Blueprint('downloads', __name__)

@downloads_bp.route('/download/<int:product_id>')
@login_required
def download(product_id):
    if current_user.sub_level == 0:
        return jsonify({"error": "Lietotājam nav plāna, lai ielādētu tēmu vai spraudni!"}), 403
    elif current_user.sub_level == 1 and current_user.downloads_remaining <= 0:
        return jsonify({"error": "Lietotājam nav atlikušas lejuplādes šodien!"}), 403

    conn = get_db_connection()
    product = conn.execute('SELECT * FROM products WHERE id = ?', (product_id,)).fetchone()
    conn.close()

    if not product:
        return jsonify({"error": "Produkts nav atrasts!"}), 404

    temp_file_path, new_filename = download_file(product)
    if not temp_file_path:
        return jsonify({"error": "Fails nav atrasts. Sazinies ar mums vai mēģini vēlāk!"}), 500

    try:
        if current_user.sub_level == 1:
            decrement_user_downloads()

        update_product_download_count(product_id)
        insert_download(current_user.id, product_id, product['version'], f"PLAN{current_user.sub_level}")

        response = send_file(
            temp_file_path,
            mimetype='application/zip',
            as_attachment=True,
            download_name=new_filename,
            conditional=True,
            etag=True
        )
        delayed_delete(temp_file_path)
        return response
    except Exception as e:
        if os.path.exists(temp_file_path):
            os.unlink(temp_file_path)
        raise e


@downloads_bp.route('/promo_download/<int:product_id>/<string:promo_code>')
@login_required
def promo_download(product_id, promo_code):
    conn = get_db_connection()
    
    recent_promo = conn.execute('''
        SELECT used_date FROM promo 
        WHERE used_by = ? 
        ORDER BY used_date DESC 
        LIMIT 1
    ''', (current_user.id,)).fetchone()

    if recent_promo and recent_promo['used_date']:
        last_promo_use = datetime.datetime.fromisoformat(recent_promo['used_date'])
        current_time = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=3)
        time_difference = current_time - last_promo_use

        remaining_time = datetime.timedelta(hours=3) - time_difference
        if time_difference < datetime.timedelta(hours=3):
            hours, remainder = divmod(remaining_time.total_seconds(), 3600)
            minutes, _ = divmod(remainder, 60)
            flash(f"Promo kodu var izmantot tikai reizi 3 stundās. Nākamo kodu vari izmantot pēc <b>{int(hours)} stundām un {int(minutes)} minūtēm.</b>", "error")
            conn.close()
    
    try:
        promo = conn.execute('SELECT * FROM promo WHERE code = ? AND used_date IS NULL AND used_by IS NULL', 
                                (promo_code,)).fetchone()
    except:
        abort(403)
    
    if not promo:
        conn.close()
        flash("Nederīgs vai jau izmantots promo kods!", "error")

    try:
        product = conn.execute('SELECT * FROM products WHERE id = ?', (product_id,)).fetchone()
        conn.close()
    except:
        abort(403)
    
    if not product:
        flash("Produkts nav atrasts!", "error")

    temp_file_path, new_filename = download_file(product)
    if not temp_file_path:
        flash("Fails nav atrasts. Sazinies ar mums vai mēģini vēlāk!", "error")

    try:
        mark_promo_code_used(promo['id'])
        update_product_download_count(product_id)
        insert_download(current_user.id, product_id, product['version'], promo_code)

        response = send_file(
            temp_file_path,
            mimetype='application/zip',
            as_attachment=True,
            download_name=new_filename,
            conditional=True,
            etag=True
        )
        delayed_delete(temp_file_path)
        flash("Promo kods veiksmīgi izmantots! Lejuplāde ir sākusies", "success")
        return response
    except Exception as e:
        if os.path.exists(temp_file_path):
            os.unlink(temp_file_path)
        flash("Kļūda lejuplādes laikā. Lūdzu, mēģiniet vēlreiz.", "error")