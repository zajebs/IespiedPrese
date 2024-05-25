from flask import Blueprint, render_template, request
from lib.database import get_db_connection

index_bp = Blueprint('index', __name__)

@index_bp.route('/')
def index():
    update = request.args.get('update', '')

    conn = get_db_connection()
    cur = conn.cursor()

    if update:
        like_clause = "name ILIKE %s"
        cur.execute(f"SELECT COUNT(*) FROM products WHERE {like_clause}", ('%' + update + '%',))
    else:
        cur.execute("SELECT COUNT(*) FROM products")

    total_count = cur.fetchone()[0]

    cur.close()
    conn.close()

    return render_template('index.html', update=update, total_count=total_count)