from flask import Flask, request, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)

# Настройка базы данных
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///temperature.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Модель для хранения температуры
class TemperatureData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    year = db.Column(db.Integer, nullable=False)
    month = db.Column(db.Integer, nullable=False)
    day = db.Column(db.Integer, nullable=False)
    temperature = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

# Создание базы данных
with app.app_context():
    db.create_all()

# Эндпоинт для получения текущей температуры
@app.route('/current_temp', methods=['GET'])
def get_current_temp():
    latest = TemperatureData.query.order_by(TemperatureData.timestamp.desc()).first()
    if latest:
        return jsonify({"temperature": latest.temperature, "timestamp": latest.timestamp})
    return jsonify({"temperature": None, "timestamp": None})

# Эндпоинт для сохранения данных от ESP32
@app.route('/data', methods=['POST'])
def receive_data():
    try:
        data = request.get_json()
        if data and 'temperature' in data:
            temperature = data['temperature']
            if not isinstance(temperature, (int, float)) or not (-50 <= temperature <= 150):
                return jsonify({"error": "Invalid temperature value"}), 400
            
            now = datetime.utcnow()
            temp_record = TemperatureData(
                year=now.year,
                month=now.month,
                day=now.day,
                temperature=temperature
            )
            db.session.add(temp_record)
            db.session.commit()
            app.logger.info(f"Temperature {temperature} saved successfully at {now}")
            return jsonify({"message": "Temperature saved successfully"}), 201
        return jsonify({"error": "Invalid data"}), 400
    except Exception as e:
        app.logger.error(f"Error processing data: {e}")
        return jsonify({"error": "Internal server error"}), 500

@app.route('/stats/<int:year>/<int:month>', methods=['GET'])
def get_monthly_stats(year, month):
    data = TemperatureData.query.filter_by(year=year, month=month).all()
    response = [{"day": t.day, "temperature": t.temperature} for t in data]
    return jsonify(response)

@app.route('/history')
def history():
    # Извлечь все данные из базы данных, отсортированные по времени
    data = TemperatureData.query.order_by(TemperatureData.timestamp.desc()).all()

    # Передать данные в шаблон
    return render_template('history.html', data=data)

@app.route('/graph')
def graph():
    # Данные для сегодняшнего графика
    today = datetime.utcnow().date()
    today_data = TemperatureData.query.filter(
        TemperatureData.year == today.year,
        TemperatureData.month == today.month,
        TemperatureData.day == today.day
    ).all()

    # Данные за текущий месяц
    month_data = TemperatureData.query.filter(
        TemperatureData.year == today.year,
        TemperatureData.month == today.month
    ).all()

    # Данные за текущий год
    year_data = TemperatureData.query.filter(
        TemperatureData.year == today.year
    ).all()

    # Преобразование данных для графиков
    graph_data = {
        "today": {
            "labels": [entry.timestamp.strftime('%H:%M:%S') for entry in today_data],
            "temperatures": [entry.temperature for entry in today_data]
        },
        "month": {
            "labels": [entry.timestamp.strftime('%d %H:%M') for entry in month_data],
            "temperatures": [entry.temperature for entry in month_data]
        },
        "year": {
            "labels": [entry.timestamp.strftime('%m-%d') for entry in year_data],
            "temperatures": [entry.temperature for entry in year_data]
        }
    }

    return render_template('graph.html', graph_data=graph_data)

# Основная страница для отображения температуры
@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
