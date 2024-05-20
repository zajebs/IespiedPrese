from flask import Blueprint, request, jsonify
from flask_login import current_user
from lib.helpers import convert_external_url_to_internal, parse_version
from lib.database import get_db_connection

products_bp = Blueprint('products', __name__)

@products_bp.route('/products', methods=['GET'])
def products():
    query = request.args.get('q', '').strip()
    order = request.args.get('o', 'dt')
    page = int(request.args.get('p', 1))
    limit = 16 if page == 1 else 4
    offset = (4 if page == 1 else 16) + (page - 2) * 4 if page > 1 else 0

    sort_by_date = "substr(last_updated, 7, 4) || '-' || substr(last_updated, 4, 2) || '-' || substr(last_updated, 1, 2)"
    if order == 'dl':
        order_string = f'downloads DESC, {sort_by_date} DESC'
    else:
        order_string = f'{sort_by_date} DESC, downloads DESC'

    conn = get_db_connection()
    
    if query:
        words = query.split()
        if words:
            like_clauses = " AND ".join(["(name LIKE ? OR category LIKE ?)"] * len(words))
            params = []
            for word in words:
                params.append('%' + word + '%')
                params.append('%' + word + '%')
            params.extend([limit, offset])

            search_query = f'''
            SELECT * FROM products
            WHERE {like_clauses}
            ORDER BY {order_string}
            LIMIT ? OFFSET ?
            '''

            product_rows = conn.execute(search_query, params).fetchall()

            count_query = f'''
            SELECT COUNT(*) FROM products
            WHERE {like_clauses}
            '''
            total = conn.execute(count_query, params[:-2]).fetchone()[0]
        else:
            search_query = f'''
            SELECT * FROM products
            ORDER BY {order_string}
            LIMIT ? OFFSET ?
            '''
            product_rows = conn.execute(search_query, (limit, offset)).fetchall()

            count_query = '''
            SELECT COUNT(*) FROM products
            '''
            total = conn.execute(count_query).fetchone()[0]
    else:
        search_query = f'''
        SELECT * FROM products
        ORDER BY {order_string}
        LIMIT ? OFFSET ?
        '''
        product_rows = conn.execute(search_query, (limit, offset)).fetchall()

        count_query = '''
        SELECT COUNT(*) FROM products
        '''
        total = conn.execute(count_query).fetchone()[0]

    conn.close()

    excluded_fields = {'id_external', 'url', 'sku_external', 'download_link'}
    
    products = []
    for row in product_rows:
        filtered_product = {key: value for key, value in dict(row).items() if key not in excluded_fields}
        filtered_product['image_url'] = convert_external_url_to_internal(filtered_product['image_url'])
        products.append(filtered_product)

    if current_user.is_authenticated:
        user_info = {
            'is_authenticated': True,
            'sub_level': current_user.sub_level,
            'downloads_remaining': 1 if current_user.sub_level == 2 else current_user.downloads_remaining
        }
    else:
        user_info = {
            'is_authenticated': False,
            'sub_level': -1,
            'downloads_remaining': 0
        }

    return jsonify({'products': products,
                    'total': total,
                    'user_info': user_info})