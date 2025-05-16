# File: app.py

from flask import Flask, render_template, jsonify, request, send_file
import sqlite3
from functools import wraps
from prometheus_client import start_http_server, Counter, generate_latest
import threading
import webbrowser
import pandas as pd
from fpdf import FPDF


app = Flask(__name__)

# Mapping sensor types to their respective units
SENSOR_UNITS = {
    "temperature": "°C",
    "humidity": "%",
    "pressure": "hPa",
    "digital": "Status"
}

# Prometheus counter for page requests
page_requests_counter = Counter('page_requests', 'Total number of requests to open the webpage', ['ip'])

# Database connection utility function
def get_db_connection():
    try:
        conn = sqlite3.connect('sensor_data.db')
        return conn
    except sqlite3.Error as e:
        raise Exception(f"Database connection error: {e}")

# Decorator for handling database query exceptions
def handle_db_error(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    return wrapper

@app.route('/')
def home():
    ip_address = request.remote_addr  # Get the IP address of the client
    page_requests_counter.labels(ip=ip_address).inc()  # Increment the counter
    return render_template('index.html')

# New route for graphical view
@app.route('/graphical')
def graphical():
    return render_template('graphical.html')

@app.route('/export-page')
def export_page():
    return render_template('export.html')


# Route to serve the tabular view HTML page
@app.route('/tabular')
def tabular_view():
    return render_template('tabular.html')
# API to fetch available buildings
@app.route('/buildings', methods=['GET'])
@handle_db_error
def get_buildings():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT DISTINCT building_id FROM sensor_data')
    rows = cursor.fetchall()
    buildings = [row[0] for row in rows]
    conn.close()
    if not buildings:
        return jsonify({"error": "No buildings found"}), 404
    return jsonify(buildings)

# API to fetch available floors
@app.route('/floors/<building_id>', methods=['GET'])
@handle_db_error
def get_floors(building_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    if building_id == 'all':
        cursor.execute('SELECT DISTINCT floor_number FROM sensor_data')
    else:
        cursor.execute('SELECT DISTINCT floor_number FROM sensor_data WHERE building_id = ?', (building_id,))
    rows = cursor.fetchall()
    conn.close()
    return jsonify([row[0] for row in rows])

# Updated sensor-types endpoint in app.py

@app.route('/sensor-types', methods=['GET'])
@handle_db_error
def get_sensor_types():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Dynamically fetch distinct sensor types from the sensor_type column
    cursor.execute('SELECT DISTINCT sensor_type FROM sensor_data')
    rows = cursor.fetchall()
    conn.close()
    
    # Convert the result to a list of sensor types
    sensor_types = [row[0] for row in rows]
    return jsonify(sensor_types)

# API to fetch sensor data
@app.route('/data/<building_id>/<floor>/<sensor_type>/<timeline>/<aggregation>', methods=['GET'])
@handle_db_error
def get_sensor_data(building_id, floor, sensor_type, timeline, aggregation):
    conn = get_db_connection()
    cursor = conn.cursor()

    # Build conditions for building and floor
    building_condition = '' if building_id == 'all' else 'AND building_id = ?'
    floor_condition = '' if floor == 'all' else 'AND floor_number = ?'
    
    params = []

    # For digital sensor type, build a query to fetch digital sensor fields
    if sensor_type == "digital":
        query = f'''
            SELECT building_id, floor_number, fan_status, rotor_status, pipe_status, fan_id
            FROM sensor_data
            WHERE sensor_type = 'digital'
            {building_condition} {floor_condition}
        '''
        if building_id != 'all':
            params.append(building_id)
        if floor != 'all':
            params.append(floor)
        cursor.execute(query, tuple(params))
        rows = cursor.fetchall()

        data = []
        for row in rows:
            data.append({
                "building_id": row[0],
                "floor_number": row[1],
                "fan_status": row[2],
                "rotor_status": row[3],
                "pipe_status": row[4],
                "fan_id": row[5],
                "unit": SENSOR_UNITS.get(sensor_type, "")
            })

    # For non-digital sensors, aggregate data by timeline
    else:
        # Determine aggregation function
        agg_function = 'AVG(CAST(value AS REAL))'
        if aggregation == 'min':
            agg_function = 'MIN(CAST(value AS REAL))'
        elif aggregation == 'max':
            agg_function = 'MAX(CAST(value AS REAL))'
            
        # Mapping for timeline formatting
        timeline_mapping = {
            'hourly': '%Y-%m-%d %H:00:00',
            'daily': '%Y-%m-%d',
            'weekly': '%Y-%W',
            'monthly': '%Y-%m',
            'yearly': '%Y'
        }
        period_format = timeline_mapping.get(timeline, '%Y-%m-%d %H:%M:%S')

        query = f'''
            SELECT strftime('{period_format}', timestamp) AS period,
                   {agg_function} AS agg_value,
                   status, fan_status, rotor_status, pipe_status
            FROM sensor_data
            WHERE sensor_type = ? {building_condition} {floor_condition}
            GROUP BY period
            ORDER BY period ASC
        '''
        # First parameter is sensor_type
        params = [sensor_type]
        if building_id != 'all':
            params.append(building_id)
        if floor != 'all':
            params.append(floor)

        cursor.execute(query, tuple(params))
        rows = cursor.fetchall()

        data = []
        for row in rows:
            data.append({
                "timestamp": row[0],
                "value": round(row[1], 2) if row[1] is not None else None,
                "status": row[2],
                "fan_status": row[3],
                "rotor_status": row[4],
                "pipe_status": row[5],
                "fan_id": None,
                "unit": SENSOR_UNITS.get(sensor_type, "")
            })

    conn.close()
    return jsonify(data)
@app.route('/tabular-data', methods=['GET'])
@handle_db_error
def get_tabular_data():
    building_id = request.args.get('building_id', 'all')
    floor_id = request.args.get('floor_id', 'all')
    sensor_type = request.args.get('sensor_type', 'all')
    timeline = request.args.get('timeline', 'raw')
    aggregation = request.args.get('aggregation', 'raw')
    limit = int(request.args.get('limit', 30))  # Default to 30 records per page
    offset = int(request.args.get('offset', 0))  # Default to start at the first record

    conn = get_db_connection()
    cursor = conn.cursor()

    # Base Query
    select_fields = '''
        building_id, 
        floor_number, 
        sensor_type, 
        strftime('%Y-%m-%d %H:%M:%S', timestamp) AS timestamp, 
        value, 
        status, 
        fan_status, 
        rotor_status, 
        pipe_status
    '''
    group_by = ''
    
    # Apply timeline grouping
    if timeline == 'hourly':
        select_fields = select_fields.replace(
            "strftime('%Y-%m-%d %H:%M:%S', timestamp)", 
            "strftime('%Y-%m-%d %H:00', timestamp)"
        )
        group_by = "GROUP BY strftime('%Y-%m-%d %H:00', timestamp), sensor_type"
    elif timeline == 'daily':
        select_fields = select_fields.replace(
            "strftime('%Y-%m-%d %H:%M:%S', timestamp)", 
            "strftime('%Y-%m-%d', timestamp)"
        )
        group_by = "GROUP BY strftime('%Y-%m-%d', timestamp), sensor_type"
    elif timeline == 'weekly':
        select_fields = select_fields.replace(
            "strftime('%Y-%m-%d %H:%M:%S', timestamp)", 
            "strftime('%Y-%W', timestamp)"
        )
        group_by = "GROUP BY strftime('%Y-%W', timestamp), sensor_type"
    elif timeline == 'monthly':
        select_fields = select_fields.replace(
            "strftime('%Y-%m-%d %H:%M:%S', timestamp)", 
            "strftime('%Y-%m', timestamp)"
        )
        group_by = "GROUP BY strftime('%Y-%m', timestamp), sensor_type"
    elif timeline == 'yearly':
        select_fields = select_fields.replace(
            "strftime('%Y-%m-%d %H:%M:%S', timestamp)", 
            "strftime('%Y', timestamp)"
        )
        group_by = "GROUP BY strftime('%Y', timestamp), sensor_type"

    # Apply aggregation
    if aggregation == 'min':
        select_fields = select_fields.replace('value', 'MIN(value) AS value')
    elif aggregation == 'max':
        select_fields = select_fields.replace('value', 'MAX(value) AS value')
    elif aggregation == 'avg':
        select_fields = select_fields.replace('value', 'AVG(value) AS value')

    # Build query
    query = f'''
        SELECT {select_fields}
        FROM sensor_data
        WHERE 1=1
    '''
    
    params = []
    
    if building_id != 'all':
        query += ' AND building_id = ?'
        params.append(building_id)
    
    if floor_id != 'all':
        query += ' AND floor_number = ?'
        params.append(floor_id)
    
    if sensor_type != 'all':
        query += ' AND sensor_type = ?'
        params.append(sensor_type)

    # Append GROUP BY and ORDER BY clauses
    if group_by:
        query += f' {group_by}'

    query += " ORDER BY timestamp DESC"
    query += f" LIMIT {limit} OFFSET {offset}"

    cursor.execute(query, tuple(params))
    rows = cursor.fetchall()
    conn.close()

    data = [
        {
                "timestamp": row[0],
                "value": round(row[1], 2) if row[1] is not None else None,
                "status": row[2],
                "fan_status": row[3],
                "rotor_status": row[4],
                "pipe_status": row[5],
                "fan_id": None,
                "unit": SENSOR_UNITS.get(sensor_type, "")
        } for row in rows
    ]

    return jsonify(data)


# Prometheus metrics    
@app.route('/metrics')
def metrics():
    return generate_latest()

# Export data route (new route)
@app.route('/export/<format>', methods=['GET'])
@handle_db_error
def export_data(format):
    conn = get_db_connection()
    df = pd.read_sql_query('SELECT * FROM sensor_data', conn)
    conn.close()

    if format == 'csv':
        return export_csv(df)
    elif format == 'excel':
        return export_excel(df)
    elif format == 'pdf':
        return export_pdf(df)
    else:
        return jsonify({"error": "Invalid format"}), 400


def export_csv(df):
    file_path = "sensor_data.csv"
    df.to_csv(file_path, index=False)
    return send_file(file_path, as_attachment=True)

def export_excel(df):
    file_path = "sensor_data.xlsx"
    df.to_excel(file_path, index=False)
    return send_file(file_path, as_attachment=True)

def export_pdf(df):
    file_path = "sensor_data.pdf"
    
    # Create a PDF instance
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="Sensor Data Report", ln=True, align='C')
    pdf.ln(10)

    # Add table header
    col_names = df.columns.tolist()
    for col in col_names:
        pdf.cell(40, 10, col, border=1)
    pdf.ln()

    # Add table rows
    for _, row in df.iterrows():
        for col in col_names:
            pdf.cell(40, 10, str(row[col]), border=1)
        pdf.ln()

    # Output PDF to file
    pdf.output(file_path)
    
    return send_file(file_path, as_attachment=True)


if __name__ == '__main__':
    port = 5000
    url = f"http://127.0.0.1:{port}/"
    # Open the browser automatically after a short delay
    threading.Timer(1.0, lambda: webbrowser.open(url)).start()
    start_http_server(8001)  # Prometheus metrics server
    app.run(host='0.0.0.0', port=port)
