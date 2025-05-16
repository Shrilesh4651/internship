from flask import Flask, render_template, jsonify, request, send_file
import sqlite3
import pandas as pd
from fpdf import FPDF
import os

app = Flask(__name__)
DB_FILE = 'simulation_data.db'
CSV_FILE = 'simulation_data.csv'
EXCEL_FILE = 'simulation_data.xlsx'
PDF_FILE = 'simulation_data.pdf'

# Utility to get database connection
def get_connection():
    return sqlite3.connect(DB_FILE)

# Fetch list of available sensors (float columns) dynamically
@app.route('/sensors', methods=['GET'])
def get_sensors():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(simulation_data);")
    cols = cursor.fetchall()
    conn.close()
    # Exclude id, timestamp, building, floor columns
    sensor_cols = [col[1] for col in cols if col[1] not in ('id', 'timestamp', 'building', 'floor')]
    return jsonify(sensor_cols)

# Fetch distinct values for a column
def distinct_vals(column):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(f'SELECT DISTINCT {column} FROM simulation_data')
    vals = [row[0] for row in cursor.fetchall()]
    conn.close()
    return vals

@app.route('/buildings', methods=['GET'])
def get_buildings():
    return jsonify(distinct_vals('building'))

@app.route('/floors', methods=['GET'])
def get_floors():
    return jsonify(distinct_vals('floor'))

# Fetch raw sensor data dynamically with optional filters
@app.route('/data/sensor/<sensor_name>', methods=['GET'])
def data_by_sensor(sensor_name):
    # Validate sensor
    sensors = get_sensors().json
    if sensor_name not in sensors:
        return jsonify({'error': 'Invalid sensor name'}), 400

    building = request.args.get('building')
    floor = request.args.get('floor')
    conn = get_connection()
    cursor = conn.cursor()
    query = f"SELECT timestamp, {sensor_name} AS value FROM simulation_data"
    params = []
    clauses = []
    if building:
        clauses.append('building = ?')
        params.append(building)
    if floor:
        clauses.append('floor = ?')
        params.append(floor)
    if clauses:
        query += ' WHERE ' + ' AND '.join(clauses)
    query += ' ORDER BY timestamp DESC'
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    data = [{'timestamp': row[0], 'value': row[1]} for row in rows]
    return jsonify(data)

# Export endpoints for entire table
@app.route('/export/csv', methods=['GET'])
def export_csv():
    df = pd.read_sql_query('SELECT * FROM simulation_data', get_connection())
    df.to_csv(CSV_FILE, index=False)
    return send_file(CSV_FILE, as_attachment=True)

@app.route('/export/excel', methods=['GET'])
def export_excel():
    df = pd.read_sql_query('SELECT * FROM simulation_data', get_connection())
    df.to_excel(EXCEL_FILE, index=False)
    return send_file(EXCEL_FILE, as_attachment=True)

@app.route('/export/pdf', methods=['GET'])
def export_pdf():
    df = pd.read_sql_query('SELECT * FROM simulation_data', get_connection())
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    col_width = pdf.w / (len(df.columns) + 1)
    # Header
    for col in df.columns:
        pdf.cell(col_width, 10, str(col), border=1)
    pdf.ln()
    # Rows
    for _, row in df.iterrows():
        for item in row:
            pdf.cell(col_width, 10, str(item), border=1)
        pdf.ln()
    pdf.output(PDF_FILE)
    return send_file(PDF_FILE, as_attachment=True)

# Routes for rendering templates
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/export')
def export_index():
    return render_template('export.html')

@app.route('/tabular')
def tabular_index():
    return render_template('tabular.html')

if __name__ == '__main__':
    # Only read data; assumes database and data already exist
    app.run(debug=True)
