from flask import Blueprint, render_template, request

index_bp = Blueprint('index', __name__)

@index_bp.route('/')
def index():
    if request.method == 'GET':
        update = request.args.get('update', '')
    return render_template('index.html', update=update)