from flask import Flask, request, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta


app = Flask(__name__)
# Настройка базы данных
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///temperature.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

pump_state = "stop"
start_temp = 45.0  # Температура для запуска управления
stop_temp = 35.0   # Температура для остановки насоса
pump_start_time = None  # Время начала работы насоса
last_pump_time = None  # Время последнего включения насоса



# Temporary cache for storing partial data
data_cache = {}


# Модель для хранения температуры
class SensorData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    temperature_in_tank = db.Column(db.Float, nullable=True)
    temperature_in_house = db.Column(db.Float, nullable=True)
    humidity_in_house = db.Column(db.Float, nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)


# Создание базы данных
with app.app_context():
    db.create_all()


# Эндпоинт для получения текущих данных
@app.route('/current_temp', methods=['GET'])
def get_current_temp():
    latest = SensorData.query.order_by(SensorData.timestamp.desc()).first()
    if latest:
        ajusted_timestamp = latest.timestamp + timedelta(hours=2)
        return jsonify({
            "temperature_in_tank": latest.temperature_in_tank,
            "temperature_in_house": latest.temperature_in_house,
            "humidity_in_house": latest.humidity_in_house,
            "timestamp": ajusted_timestamp.strftime('%Y-%m-%d %H:%M:%S')
        })
    return jsonify({
        "temperature_in_tank": None,
        "temperature_in_house": None,
        "humidity_in_house": None,
        "timestamp": None
    })
    

def temp_check(temperature):
    global pump_state, pump_start_time, last_pump_time
    current_time = time.time()
    
    # Проверка температуры для запуска
    if temperature >= start_temp and pump_state == "stop":
        if last_pump_time is None or (current_time - last_pump_time) >= 30 * 60:
            pump_state = "start"
            pump_start_time = current_time
            last_pump_time = current_time
    
    # Проверка времени работы насоса
    if pump_state == "start" and pump_start_time:
        if (current_time - pump_start_time) >= 15 * 60:
            pump_state = "stop"
            pump_start_time = None
    
    # Проверка температуры для остановки
    if temperature < stop_temp:
        pump_state = "stop"
        pump_start_time = None

# Эндпоинт для сохранения данных от ESP32
@app.route('/data', methods=['POST'])
def receive_data():
    global pump_state
    try:
        # Get JSON from request
        data = request.get_json()
        print(f"Received raw JSON: {data}")  # Debugging

        if not data or 'source' not in data:
            return jsonify({"error": "Missing 'source' field"}), 400
        
        source = data['source']

        # Validate ESP32 temperature data
        if source == "esp32_tank" and 'temperature_in_tank' in data:
            data_cache['temperature_in_tank'] = data['temperature_in_tank']
            print(f"Stored temperature_in_tank: {data_cache['temperature_in_tank']}")  # Debugging
        elif source == "raspberry_pi_home" and 'temperature_in_house' in data and 'humidity_in_house' in data:
            data_cache['temperature_in_house'] = data['temperature_in_house']
            data_cache['humidity_in_house'] = data['humidity_in_house']
            print(f"Stored temperature_in_house: {data_cache['temperature_in_house']}")  # Debugging
        else:
            return jsonify({"error": "Invalid or incomplete data for source"}), 400

        # Ensure all data is available before processing
        if 'temperature_in_tank' in data_cache:
            print(f"Processing temperature_in_tank: {data_cache['temperature_in_tank']}")  # Debugging
            temp_check(data_cache['temperature_in_tank'])  # Use stored value instead of data['temperature_in_tank']

            # Insert into database if all values are available
            if all(key in data_cache for key in ['temperature_in_tank', 'temperature_in_house', 'humidity_in_house']):
                entry = SensorData(
                    temperature_in_tank=data_cache['temperature_in_tank'],
                    temperature_in_house=data_cache['temperature_in_house'],
                    humidity_in_house=data_cache['humidity_in_house']
                )
                db.session.add(entry)
                db.session.commit()
                print("Data committed to database.")  # Debugging

            # Clear the cache after processing
            data_cache.clear()
            return jsonify({"command": pump_state})
        
        return jsonify({"message": "Partial data received, waiting for more"}), 200
    except Exception as e:
        app.logger.error(f"Error processing data: {e}")
        return jsonify({"error": "Internal server error"}), 500


# @app.route('/data/<string:date>', methods=['GET'])
# def get_data_by_day(date):
#     try:
#         # Parse the date
#         selected_date = datetime.strptime(date, '%Y-%m-%d').date()
#         data = SensorData.query.filter(
#             db.func.date(SensorData.timestamp) == selected_date
#         ).all()

#         # Convert data to a list of dictionaries
#         result = [
#             {
#                 "timestamp": entry.timestamp.strftime('%H:%M:%S'),
#                 "temperature_in_tank": entry.temperature_in_tank,
#                 "temperature_in_house": entry.temperature_in_house,
#                 "humidity_in_house": entry.humidity_in_house,
#             }
#             for entry in data
#         ]

#         return jsonify(result)
#     except ValueError:
#         return jsonify({"error": "Invalid date format. Use YYYY-MM-DD."}), 400
#     except Exception as e:
#         app.logger.error(f"Error fetching data: {e}")
#         return jsonify({"error": "Internal server error"}), 500


@app.route('/graph')
def graph():
    return render_template('home.html')


@app.route('/pump', methods=['GET', 'POST'])
def pump():
    global pump_state
    print(f'pump status: {pump_state}')
    if request.method == 'POST':
        pump_state = "stop" if pump_state == "start" else "start"
        return pump_state  # Возвращаем новое состояние
    return render_template('pump.html', pump_state=pump_state)


# Основная страница для отображения температуры
@app.route('/')
def home():
    return render_template('home.html')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
