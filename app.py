from flask import Flask, render_template, jsonify, send_file
import sqlite3
import random
from datetime import datetime
import threading
import time
import webbrowser
import pandas as pd
from fpdf import FPDF
import os

app = Flask(__name__)

DB_FILE = 'sensor_data.db'
CSV_FILE = 'sensor_data.csv'
EXCEL_FILE = 'sensor_data.xlsx'
PDF_FILE = 'sensor_data.pdf'

# Initialize SQLite Database
def init_db():
    conn = sqlite3.connect(DB_FILE)
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

# Insert random sensor data into the database
def insert_random_data():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    building_id = random.randint(1, 10)
    sensor_id = random.randint(1, 5)
    sensor_type = random.choice(["temperature", "humidity", "pressure"])
    value = (
        random.uniform(20, 35)
        if sensor_type == "temperature"
        else random.uniform(30, 60)
    )
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute(
        '''
        INSERT INTO sensor_data (building_id, sensor_id, sensor_type, value, timestamp)
        VALUES (?, ?, ?, ?, ?)
        ''',
        (building_id, sensor_id, sensor_type, value, timestamp),
    )

    conn.commit()
    conn.close()

# Background thread to continuously update the database
def continuous_update():
    while True:
        insert_random_data()
        time.sleep(5)

# API to fetch available buildings
@app.route('/buildings', methods=['GET'])
def get_buildings():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('SELECT DISTINCT building_id FROM sensor_data')
    rows = cursor.fetchall()
    conn.close()
    buildings = [row[0] for row in rows]
    return jsonify(buildings)

# API to fetch available sensor types
@app.route('/sensor-types', methods=['GET'])
def get_sensor_types():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('SELECT DISTINCT sensor_type FROM sensor_data')
    rows = cursor.fetchall()
    conn.close()
    sensor_types = [row[0] for row in rows]
    return jsonify(sensor_types)

# API to fetch sensor data with timeline filtering
@app.route('/data/<building_id>/<sensor_type>/<timeline>', methods=['GET'])
def get_sensor_data_with_timeline(building_id, sensor_type, timeline):
    conn = sqlite3.connect(DB_FILE)
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
    conn = sqlite3.connect(DB_FILE)
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
@app.route('/export')
def export_index():
    return render_template('export.html')
@app.route('/tabular')
def tabular_index():
    return render_template('tabular.html')

# API to fetch all sensor data (for table)
@app.route('/api/data', methods=['GET'])
def api_data():
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query("SELECT * FROM sensor_data ORDER BY timestamp DESC", conn)
    conn.close()
    return jsonify(df.to_dict(orient='records'))

# Export to CSV
@app.route('/export/csv', methods=['GET'])
def export_csv():
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query("SELECT * FROM sensor_data ORDER BY timestamp", conn)
    conn.close()
    df.to_csv(CSV_FILE, index=False)
    return send_file(CSV_FILE, as_attachment=True)

# Export to Excel
@app.route('/export/excel', methods=['GET'])
def export_excel():
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query("SELECT * FROM sensor_data ORDER BY timestamp", conn)
    conn.close()
    df.to_excel(EXCEL_FILE, index=False)
    return send_file(EXCEL_FILE, as_attachment=True)

# Export to PDF
@app.route('/export/pdf', methods=['GET'])
def export_pdf():
    if os.path.exists(PDF_FILE):
        os.remove(PDF_FILE)

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM sensor_data ORDER BY timestamp")
    rows = cursor.fetchall()
    conn.close()

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Arial", size=10)

    # Header
    pdf.cell(0, 8, "Sensor Data Export", ln=True, align='C')
    pdf.ln(4)

    # Column titles
    col_widths = [10, 20, 20, 30, 20, 40]
    headers = ["ID", "Building", "Sensor", "Type", "Value", "Timestamp"]
    for i, title in enumerate(headers):
        pdf.cell(col_widths[i], 8, title, border=1)
    pdf.ln()

    # Data rows
    for row in rows:
        for idx, cell in enumerate(row):
            pdf.cell(col_widths[idx], 8, str(cell), border=1)
        pdf.ln()

    pdf.output(PDF_FILE)
    return send_file(PDF_FILE, as_attachment=True)

# Home route to serve the HTML dashboard
@app.route('/')
def home():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('SELECT DISTINCT building_id FROM sensor_data')
    buildings = cursor.fetchall()
    cursor.execute('SELECT DISTINCT sensor_type FROM sensor_data')
    sensor_types = cursor.fetchall()
    conn.close()
    return render_template('index.html', buildings=buildings, sensor_types=sensor_types)

if __name__ == '__main__':
    init_db()
    thread = threading.Thread(target=continuous_update, daemon=True)
    thread.start()
    threading.Timer(1.0, lambda: webbrowser.open("http://127.0.0.1:5000/")).start()
    app.run(debug=True)
