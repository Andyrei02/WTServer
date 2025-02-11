from flask import Flask, request, jsonify

app = Flask(__name__)

# Default temperature thresholds and intervals
temp_to_start = 45.0
temp_to_stop = 35.0
run_interval = 15  # Minutes to run
pause_interval = 60  # Minutes to pause
pump_running = False

def decide_pump_action(temperature):
    global pump_running
    
    if temperature >= temp_to_start and not pump_running:
        pump_running = True
        return {"command": "start", "temp_to_start": temp_to_start, "temp_to_stop": temp_to_stop,
                "run_interval": run_interval, "pause_interval": pause_interval}
    elif temperature <= temp_to_stop and pump_running:
        pump_running = False
        return {"command": "stop", "temp_to_start": temp_to_start, "temp_to_stop": temp_to_stop,
                "run_interval": run_interval, "pause_interval": pause_interval}
    return {"command": "none"}

@app.route("/data", methods=["POST"])
def receive_data():
    data = request.get_json()
    if not data or "temperature_in_tank" not in data:
        return jsonify({"error": "Invalid data"}), 400
    
    temperature = data["temperature_in_tank"]
    print(f"Received temperature: {temperature}°C")
    
    response = decide_pump_action(temperature)
    return jsonify(response)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
