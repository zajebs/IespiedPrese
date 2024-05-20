from flask import Blueprint, request, jsonify
from flask_login import current_user
from lib.helpers import convert_external_url_to_amazon
from lib.database import get_db_connection

products_bp = Blueprint('products', __name__)

@products_bp.route('/products', methods=['GET'])
def products():
    query = request.args.get('q', '').strip()
    order = request.args.get('o', 'dt')
    page = int(request.args.get('p', 1))
    limit = 16 if page == 1 else 4
    offset = (4 if page == 1 else 16) + (page - 2) * 4 if page > 1 else 0

    sort_by_date = "TO_DATE(last_updated, 'DD.MM.YYYY')"
    if order == 'dl':
        order_string = f'downloads DESC, {sort_by_date} DESC'
    else:
        order_string = f'{sort_by_date} DESC, downloads DESC'

    conn = get_db_connection()
    cur = conn.cursor()

    if query:
        words = query.split()
        if words:
            like_clauses = " AND ".join(["(name ILIKE %s OR category ILIKE %s)"] * len(words))
            params = []
            for word in words:
                params.append('%' + word + '%')
                params.append('%' + word + '%')
            params.extend([limit, offset])

            search_query = f'''
            SELECT * FROM products
            WHERE {like_clauses}
            ORDER BY {order_string}
            LIMIT %s OFFSET %s
            '''

            cur.execute(search_query, tuple(params))
            product_rows = cur.fetchall()

            count_query = f'''
            SELECT COUNT(*) FROM products
            WHERE {like_clauses}
            '''
            cur.execute(count_query, tuple(params[:-2]))
            total = cur.fetchone()[0]
        else:
            search_query = f'''
            SELECT * FROM products
            ORDER BY {order_string}
            LIMIT %s OFFSET %s
            '''
            cur.execute(search_query, (limit, offset))
            product_rows = cur.fetchall()

            count_query = '''
            SELECT COUNT(*) FROM products
            '''
            cur.execute(count_query)
            total = cur.fetchone()[0]
    else:
        search_query = f'''
        SELECT * FROM products
        ORDER BY {order_string}
        LIMIT %s OFFSET %s
        '''
        cur.execute(search_query, (limit, offset))
        product_rows = cur.fetchall()

        count_query = '''
        SELECT COUNT(*) FROM products
        '''
        cur.execute(count_query)
        total = cur.fetchone()[0]

    column_mappings = {
        0: 'id',
        1: 'name',
        3: 'category',
        5: 'image_url',
        6: 'version',
        7: 'last_updated',
        10: 'downloads'
    }

    products = []
    for row in product_rows:
        filtered_product = {column_mappings[idx]: value for idx, value in enumerate(row) if idx in column_mappings}
        if 'image_url' in filtered_product:
            filtered_product['image_url'] = convert_external_url_to_amazon(filtered_product['image_url'])
        products.append(filtered_product)

    cur.close()
    conn.close()

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
