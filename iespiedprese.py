import os
import re
from flask import Flask, send_from_directory, request, jsonify, render_template
from flask_bcrypt import Bcrypt
from flask_htmlmin import HTMLMIN
from lib.config import SECRET_KEY
from lib.login_manager import init_login_manager
from lib.blueprints import register_blueprints
from lib.helpers import str_to_bool
from dotenv import load_dotenv
from flask_squeeze import Squeeze
from datetime import datetime, timedelta
from googleapiclient.discovery import build

squeeze = Squeeze()
load_dotenv()
PORT = int(os.getenv('PORT'))
DEBUG = str_to_bool(os.getenv('DEBUG', 'False'))
CACHE_AGE = int(os.getenv('CACHE_AGE'))
GA_MEASUREMENT_ID = (os.getenv('GA_MEASUREMENT_ID'))
SPECIFIC_PATH = (os.getenv('SPECIFIC_PATH'))
GOOGLE_API_KEY = (os.getenv('GOOGLE_API_KEY'))
GOOGLE_SPREADSHEET_ID = (os.getenv('GOOGLE_SPREADSHEET_ID'))
GOOGLE_RANGE_NAME = (os.getenv('GOOGLE_RANGE_NAME'))
GOOGLE_RESULTS_RANGE = (os.getenv('GOOGLE_RESULTS_RANGE'))
GOOGLE_PLAYER_RANGE = (os.getenv('GOOGLE_PLAYER_RANGE'))

def remove_emoji(text):
    return re.sub(r'[^\w\s,.-]', '', text)

def create_app():
    app = Flask(__name__)
    squeeze.init_app(app)
    app.secret_key = SECRET_KEY
    app.config['MINIFY_HTML'] = True
    HTMLMIN(app)
    Bcrypt(app)
    init_login_manager(app)
    register_blueprints(app)

    @app.context_processor
    def inject_ga_measurement_id():
        return dict(GA_MEASUREMENT_ID=GA_MEASUREMENT_ID, SPECIFIC_PATH=SPECIFIC_PATH)

    @app.after_request
    def add_header(response):
        if request.path.startswith('/static/'):
            expires = datetime.utcnow() + timedelta(days=CACHE_AGE)
            response.headers['Expires'] = expires.strftime("%a, %d %b %Y %H:%M:%S GMT")
            response.headers['Cache-Control'] = f'public, max-age={CACHE_AGE*60*60*24}'
        return response

    @app.route('/static/<path:filename>')
    def custom_static(filename):
        response = send_from_directory(app.static_folder, filename)
        expires = datetime.utcnow() + timedelta(days=CACHE_AGE)
        response.headers['Expires'] = expires.strftime("%a, %d %b %Y %H:%M:%S GMT")
        response.headers['Cache-Control'] = f'public, max-age={CACHE_AGE*60*60*24}'
        return response
    
    @app.route('/robots.txt')
    def robots_txt():
        return send_from_directory(app.static_folder, 'robots.txt')

    @app.route('/la-familia', methods=['GET'])
    def get_table():
        try:
            service = build('sheets', 'v4', developerKey=GOOGLE_API_KEY)
            sheet = service.spreadsheets()

            result = sheet.values().get(spreadsheetId=GOOGLE_SPREADSHEET_ID,
                                        range=GOOGLE_RANGE_NAME).execute()
            values = result.get('values', [])

            if not values:
                return jsonify({"error": "No data found in Leaderbord."})

            results_data = sheet.values().get(spreadsheetId=GOOGLE_SPREADSHEET_ID,
                                            range=GOOGLE_RESULTS_RANGE).execute()
            results_values = results_data.get('values', [])

            if not results_values:
                return jsonify({"error": "No data found in Results."})

            last_updated_game = None
            for row in results_values:
                if len(row) > 7 and row[7] != "TBD":
                    last_updated_game = row[:4]

            if not last_updated_game:
                return jsonify({"error": "No updated game found."})

            values = sorted(values, key=lambda x: float(x[1].replace(',', '.')), reverse=True)
            ranks = []
            previous_value = None
            previous_rank = 0
            for index, (name, value) in enumerate(values):
                current_value = float(value.replace(',', '.'))
                if current_value == previous_value:
                    rank = previous_rank
                else:
                    rank = index + 1
                cleaned_name = remove_emoji(name)
                if current_value > 0:
                    formatted_value = f"+€{value}"
                else:
                    formatted_value = f"-€{abs(current_value):,.2f}".replace('.', ',')
                ranks.append((rank, cleaned_name, formatted_value))
                previous_value = current_value
                previous_rank = rank

            return render_template('leaderboard.html', data=ranks, last_updated_game=last_updated_game)
        except Exception as e:
            return jsonify({"error": str(e)})

    @app.route('/player/<name>', methods=['GET'])
    def get_player_data(name):
        try:
            service = build('sheets', 'v4', developerKey=GOOGLE_API_KEY)
            sheet = service.spreadsheets()
            headers_data = sheet.values().get(spreadsheetId=GOOGLE_SPREADSHEET_ID,
                                            range='Results!I1:T1').execute()
            headers = headers_data.get('values', [])[0]

            player_index = None
            for i, header in enumerate(headers):
                if header.strip().lower() == name.lower():
                    player_index = i
                    break

            if player_index is None:
                return jsonify({"error": "Player not found."})

            column_index = player_index + 8

            all_results_data = sheet.values().get(spreadsheetId=GOOGLE_SPREADSHEET_ID,
                                                range='Results!A:T').execute()
            all_results_values = all_results_data.get('values', [])

            if not all_results_values:
                return jsonify({"error": "No data found in Results."})

            total_games = 0
            for row in all_results_values[1:]:
                if len(row) > 7 and row[7] and row[7] != 'TBD':
                    total_games += 1

            results_data = sheet.values().get(spreadsheetId=GOOGLE_SPREADSHEET_ID,
                                            range=GOOGLE_PLAYER_RANGE).execute()
            results_values = results_data.get('values', [])

            if not results_values:
                return jsonify({"error": "No data found in Results."})

            data = []
            for row in results_values:
                if len(row) > column_index:
                    result = row[7] if len(row) > 7 else None
                    if result and result != 'TBD':
                        prediction = row[column_index] if len(row) > column_index else None
                        if prediction:
                            win = result == prediction if result and prediction else False
                            money = 0
                            if win:
                                if prediction == "1":
                                    money = round((float(row[4].replace(',', '.')) - 1) * 10, 2)
                                elif prediction == "x":
                                    money = round((float(row[5].replace(',', '.')) - 1) * 10, 2)
                                elif prediction == "2":
                                    money = round((float(row[6].replace(',', '.')) - 1) * 10, 2)
                            else:
                                money = -10

                            game_data = {
                                "date": row[0] if len(row) > 0 else "",
                                "time": row[1] if len(row) > 1 else "",
                                "home": row[2] if len(row) > 2 else "",
                                "away": row[3] if len(row) > 3 else "",
                                "odds1": row[4] if len(row) > 4 else "",
                                "oddsX": row[5] if len(row) > 5 else "",
                                "odds2": row[6] if len(row) > 6 else "",
                                "result": result,
                                "prediction": prediction,
                                "win": win,
                                "money": money
                            }
                            data.append(game_data)

            male = not name.endswith('a')
            placed = ""
            placed_games = len(data)
            placed_percentage = (placed_games / total_games) * 100 if total_games > 0 else 0
            placed_percentage = int(placed_percentage)
            sentence = ""
            if placed_percentage < 50:
                sentence = "Nepiedalās apbalvošanā"
            elif 50 <= placed_percentage < 75:
                if male:
                    sentence = "Varētu būt aktīvāks"
                else:
                    sentence = "Varētu būt aktīvāka"
            elif 76 <= placed_percentage < 99:
                sentence = "Lieliska aktivitāte"
            else:
                if male:
                    sentence = "Nav izlaidis NEVIENU spēli"
                else:
                    sentence = "Nav izlaidusi NEVIENU spēli"
            if male:
                placed = "Veicis"
            else:
                placed = "Veikusi"

            return render_template('player.html', data=data, player=name, total_games=total_games, placed_games=placed_games, placed_percentage=placed_percentage, sentence=sentence, placed=placed)
        except Exception as e:
            return jsonify({"error": str(e)})

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=PORT, debug=DEBUG)
