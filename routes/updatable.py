from flask import Blueprint, jsonify
from flask_login import login_required, current_user
from lib.helpers import parse_version
from lib.database import get_db_connection

updatable_bp = Blueprint('updatable', __name__)

@updatable_bp.route('/updatable', methods=['GET'])
@login_required
def updatable():
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute('''
            SELECT downloads.id, products.name as product_name, downloads.version as downloaded_version, products.version as current_version
            FROM downloads
            JOIN products ON downloads.product_id = products.id
            WHERE downloads.user_id = ?
            ORDER BY downloads.utc_date DESC
        ''', (current_user.id,))
        all_downloads = cur.fetchall()
        
        latest_versions = {}
        updatable_count = 0

        for row in all_downloads:
            product_name = row['product_name']
            downloaded_version = row['downloaded_version']
            current_version = row['current_version']
            
            if product_name not in latest_versions or parse_version(downloaded_version) > parse_version(latest_versions[product_name]):
                latest_versions[product_name] = downloaded_version

        for row in all_downloads:
            product_name = row['product_name']
            downloaded_version = row['downloaded_version']
            current_version = row['current_version']
            
            if (downloaded_version == latest_versions[product_name]) and (parse_version(downloaded_version) < parse_version(current_version)):
                updatable_count += 1

    finally:
        conn.close()

    return jsonify({'updatable_count': updatable_count})