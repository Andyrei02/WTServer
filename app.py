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
    data = request.get_json()
    if data and 'temperature' in data:
        now = datetime.utcnow()
        temp_record = TemperatureData(
            year=now.year,
            month=now.month,
            day=now.day,
            temperature=data['temperature']
        )
        db.session.add(temp_record)
        db.session.commit()
        return jsonify({"message": "Temperature saved successfully"}), 201
    return jsonify({"error": "Invalid data"}), 400

@app.route('/stats/<int:year>/<int:month>', methods=['GET'])
def get_monthly_stats(year, month):
    data = TemperatureData.query.filter_by(year=year, month=month).all()
    response = [{"day": t.day, "temperature": t.temperature} for t in data]
    return jsonify(response)

# Основная страница для отображения температуры
@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
