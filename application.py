from flask import Flask, render_template, jsonify
import sqlite3
import webbrowser
import threading

app = Flask(__name__)

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
    port = 5000  # Port on which the Flask app will run
    url = f"http://127.0.0.1:{port}/"
    threading.Timer(1.0, lambda: webbrowser.open(url)).start()

    # Start the Flask application
    app.run(debug=True)
