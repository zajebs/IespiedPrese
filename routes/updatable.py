from flask import Blueprint, jsonify
from flask_login import login_required, current_user
from lib.helpers import fetch_all_downloads_for_user, get_latest_versions, count_updatable_products

updatable_bp = Blueprint('updatable', __name__)

@updatable_bp.route('/updatable', methods=['GET'])
@login_required
def updatable():
    all_downloads = fetch_all_downloads_for_user(current_user.id)
    latest_versions = get_latest_versions(all_downloads)
    updatable_count = count_updatable_products(all_downloads, latest_versions)
    return jsonify({'updatable_count': updatable_count})