from flask import Flask, render_template, jsonify
import sqlite3
import random
from datetime import datetime
import threading
import time
import webbrowser

app = Flask(__name__)

# Initialize SQLite Database
def init_db():
    conn = sqlite3.connect('sensor_data.db')
    cursor = conn.cursor()
    cursor.execute(''' 
        CREATE TABLE IF NOT EXISTS sensor_data ( 
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            building_id INTEGER, 
            sensor_id INTEGER, 
            sensor_type TEXT, 
            value REAL, 
            timestamp TEXT 
        ) 
    ''')
    conn.commit()
    conn.close()

# Function to insert random sensor data into the database
def insert_random_data():
    conn = sqlite3.connect('sensor_data.db')
    cursor = conn.cursor()

    building_id = random.randint(1, 10)  # Dynamic for up to 10 buildings
    sensor_id = random.randint(1, 5)  # Sensor IDs from 1 to 5
    sensor_type = random.choice(["temperature", "humidity", "pressure"])
    value = random.uniform(20, 35) if sensor_type == "temperature" else random.uniform(30, 60)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute(''' 
        INSERT INTO sensor_data (building_id, sensor_id, sensor_type, value, timestamp)
        VALUES (?, ?, ?, ?, ?)
    ''', (building_id, sensor_id, sensor_type, value, timestamp))

    conn.commit()
    conn.close()

# Background thread to continuously update the database
def continuous_update():
    while True:
        insert_random_data()
        time.sleep(5)  # Add new data every 5 seconds

# API to fetch available buildings
@app.route('/buildings', methods=['GET'])
def get_buildings():
    conn = sqlite3.connect('sensor_data.db')
    cursor = conn.cursor()
    cursor.execute('SELECT DISTINCT building_id FROM sensor_data')
    rows = cursor.fetchall()
    conn.close()
    buildings = [row[0] for row in rows]
    return jsonify(buildings)

# API to fetch available sensor types
@app.route('/sensor-types', methods=['GET'])
def get_sensor_types():
    conn = sqlite3.connect('sensor_data.db')
    cursor = conn.cursor()
    cursor.execute('SELECT DISTINCT sensor_type FROM sensor_data')
    rows = cursor.fetchall()
    conn.close()
    sensor_types = [row[0] for row in rows]
    return jsonify(sensor_types)

# API to fetch sensor data with timeline filtering
@app.route('/data/<building_id>/<sensor_type>/<timeline>', methods=['GET'])
def get_sensor_data_with_timeline(building_id, sensor_type, timeline):
    conn = sqlite3.connect('sensor_data.db')
    cursor = conn.cursor()

    if timeline == 'hourly':
        query = '''
            SELECT strftime('%Y-%m-%d %H:00:00', timestamp) AS period, AVG(value)
            FROM sensor_data
            WHERE building_id = ? AND sensor_type = ?
            GROUP BY period
            ORDER BY period DESC
        '''
    elif timeline == 'daily':
        query = '''
            SELECT strftime('%Y-%m-%d', timestamp) AS period, AVG(value)
            FROM sensor_data
            WHERE building_id = ? AND sensor_type = ?
            GROUP BY period
            ORDER BY period DESC
        '''
    else:  # Default to raw data
        query = '''
            SELECT timestamp, value
            FROM sensor_data
            WHERE building_id = ? AND sensor_type = ?
            ORDER BY timestamp DESC
        '''

    cursor.execute(query, (building_id, sensor_type))
    rows = cursor.fetchall()
    conn.close()

    data = [{"timestamp": row[0], "value": row[1]} for row in rows]
    return jsonify(data)

# API to fetch sensor type distribution
@app.route('/sensor-distribution', methods=['GET'])
def get_sensor_distribution():
    conn = sqlite3.connect('sensor_data.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT sensor_type, COUNT(*)
        FROM sensor_data
        GROUP BY sensor_type
    ''')
    rows = cursor.fetchall()
    conn.close()

    distribution = [{"sensor_type": row[0], "count": row[1]} for row in rows]
    return jsonify(distribution)

# Home route to serve the HTML dashboard
@app.route('/')
def home():
    conn = sqlite3.connect('sensor_data.db')
    cursor = conn.cursor()
    cursor.execute('SELECT DISTINCT building_id FROM sensor_data')
    buildings = cursor.fetchall()
    cursor.execute('SELECT DISTINCT sensor_type FROM sensor_data')
    sensor_types = cursor.fetchall()
    conn.close()

    # Pass the fetched buildings and sensor types to the HTML template
    return render_template('index.html', buildings=buildings, sensor_types=sensor_types)

if __name__ == '__main__':
    init_db()

    # Start the background thread
    thread = threading.Thread(target=continuous_update, daemon=True)
    thread.start()

    # Automatically open the index.html in the default web browser
    port = 5000  # Port on which the Flask app will run
    url = f"http://127.0.0.1:{port}/"
    threading.Timer(1.0, lambda: webbrowser.open(url)).start()

    # Start the Flask application
    app.run(debug=True)
