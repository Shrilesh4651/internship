from flask import Flask, render_template, jsonify, request, send_file, session, redirect, url_for
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.exc import SQLAlchemyError
import pandas as pd
from fpdf import FPDF
import tempfile
import os
import logging
from functools import wraps

app = Flask(__name__)
app.secret_key = "super-secret-key"  # Needed for session handling

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ----------- Middleware: Require DB before access -----------
def db_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'db_url' not in session:
            return redirect(url_for('configure_db_form'))
        return f(*args, **kwargs)
    return decorated_function

# ----------- Utility: Get SQLAlchemy Engine -----------
def get_db_engine():
    db_url = session.get('db_url')
    if not db_url:
        raise RuntimeError("Database URL not configured in session.")
    engine = create_engine(db_url)
    # Defensive check for table existence
    inspector = inspect(engine)
    if 'simulation_data' not in inspector.get_table_names():
        raise RuntimeError("Table 'simulation_data' does not exist in the database.")
    return engine

# ----------- DB Configuration Page (GET) -----------
@app.route('/configure-db', methods=['GET'])
def configure_db_form():
    # Render your configure_db.html where user inputs DB info (type, host, etc.)
    return render_template('configure_db.html')

# ----------- DB Configuration Submit (POST) -----------
@app.route('/configure-db', methods=['POST'])
def configure_db():
    data = request.json
    db_type = data.get('type')
    host = data.get('host')
    port = data.get('port')
    user = data.get('user')
    password = data.get('password')
    db_name = data.get('database')

    # Compose DB URL based on type
    if db_type == 'sqlite':
        db_file_path = f"{db_name}.db"
        if not os.path.exists(db_file_path):
            return jsonify({'error': f"SQLite DB file '{db_file_path}' does not exist."}), 400
        db_url = f"sqlite:///{os.path.abspath(db_file_path)}"  # Use absolute path
    elif db_type == 'mysql':
        db_url = f"mysql+pymysql://{user}:{password}@{host}:{port}/{db_name}"
    elif db_type == 'postgresql':
        db_url = f"postgresql://{user}:{password}@{host}:{port}/{db_name}"
    else:
        return jsonify({'error': 'Unsupported DB type'}), 400

    try:
        engine = create_engine(db_url)
        with engine.connect() as conn:
            # Test connection
            conn.execute(text("SELECT 1"))
            # Check for required table
            inspector = inspect(engine)
            if 'simulation_data' not in inspector.get_table_names():
                return jsonify({'error': "Table 'simulation_data' does not exist in the database."}), 400

        session['db_url'] = db_url
        logger.info(f"Connected to database: {db_url}")
        return jsonify({'message': 'Database connected successfully', 'redirect': url_for('home')})
    except SQLAlchemyError as e:
        logger.error(f"DB connection error: {str(e)}")
        return jsonify({'error': str(e)}), 500

# ----------- Pages (require DB config) -----------
@app.route('/')
@db_required
def home():
    return render_template('index.html')

@app.route('/tabular')
@db_required
def tabular_index():
    return render_template('tabular.html')

@app.route('/export')
@db_required
def export_index():
    return render_template('export.html')

# ----------- API Routes -----------
@app.route('/sensors', methods=['GET'])
@db_required
def get_sensors():
    try:
        engine = get_db_engine()
        inspector = inspect(engine)
        columns = inspector.get_columns('simulation_data')
        sensor_cols = [col['name'] for col in columns if col['name'] not in ('id', 'timestamp', 'building', 'floor')]
        return jsonify(sensor_cols)
    except Exception as e:
        logger.error(f"Error fetching sensors: {str(e)}")
        return jsonify({'error': str(e)}), 500

def distinct_vals(column):
    try:
        engine = get_db_engine()
        query = text(f"SELECT DISTINCT {column} FROM simulation_data")
        with engine.connect() as conn:
            result = conn.execute(query)
            return [row[0] for row in result]
    except Exception as e:
        logger.error(f"Error fetching distinct values for {column}: {str(e)}")
        return []

@app.route('/buildings', methods=['GET'])
@db_required
def get_buildings():
    return jsonify(distinct_vals('building'))

@app.route('/floors', methods=['GET'])
@db_required
def get_floors():
    return jsonify(distinct_vals('floor'))

@app.route('/data/sensor/<sensor_name>', methods=['GET'])
@db_required
def data_by_sensor(sensor_name):
    building = request.args.get('building')
    floor = request.args.get('floor')

    try:
        engine = get_db_engine()
        inspector = inspect(engine)
        sensor_list = [col['name'] for col in inspector.get_columns('simulation_data')]

        if sensor_name not in sensor_list:
            return jsonify({'error': 'Invalid sensor name'}), 400

        query = f"SELECT timestamp, {sensor_name} AS value FROM simulation_data"
        filters = []
        params = {}

        if building:
            filters.append("building = :building")
            params['building'] = building
        if floor:
            filters.append("floor = :floor")
            params['floor'] = floor

        if filters:
            query += " WHERE " + " AND ".join(filters)

        query += " ORDER BY timestamp DESC"

        with engine.connect() as conn:
            result = conn.execute(text(query), params)
            # FIXED: Use row._mapping to access by column names
            data = [{'timestamp': row._mapping['timestamp'], 'value': row._mapping['value']} for row in result]

        return jsonify(data)

    except Exception as e:
        logger.error(f"Error fetching sensor data: {str(e)}")
        return jsonify({'error': str(e)}), 500

# ----------- Export Endpoints -----------
@app.route('/export/csv', methods=['GET'])
@db_required
def export_csv():
    tmp_path = None
    try:
        df = pd.read_sql('SELECT * FROM simulation_data', get_db_engine())
        with tempfile.NamedTemporaryFile(delete=False, suffix='.csv') as tmp:
            df.to_csv(tmp.name, index=False)
            tmp_path = tmp.name
        return send_file(tmp_path, as_attachment=True, download_name='simulation_data.csv')
    finally:
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except Exception as e:
                logger.warning(f"Failed to delete temp file: {tmp_path}, error: {e}")

@app.route('/export/excel', methods=['GET'])
@db_required
def export_excel():
    tmp_path = None
    try:
        df = pd.read_sql('SELECT * FROM simulation_data', get_db_engine())
        with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp:
            df.to_excel(tmp.name, index=False)
            tmp_path = tmp.name
        return send_file(tmp_path, as_attachment=True, download_name='simulation_data.xlsx')
    finally:
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except Exception as e:
                logger.warning(f"Failed to delete temp file: {tmp_path}, error: {e}")

@app.route('/export/pdf', methods=['GET'])
@db_required
def export_pdf():
    tmp_path = None
    try:
        df = pd.read_sql('SELECT * FROM simulation_data', get_db_engine())
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=10)
        col_width = pdf.w / (len(df.columns) + 1)

        # Header
        for col in df.columns:
            pdf.cell(col_width, 10, str(col), border=1)
        pdf.ln()

        # Rows
        for _, row in df.iterrows():
            for item in row:
                text = str(item)
                if len(text) > 15:
                    text = text[:12] + "..."
                pdf.cell(col_width, 10, text, border=1)
            pdf.ln()

        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
            pdf.output(tmp.name)
            tmp_path = tmp.name

        return send_file(tmp_path, as_attachment=True, download_name='simulation_data.pdf')
    finally:
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except Exception as e:
                logger.warning(f"Failed to delete temp file: {tmp_path}, error: {e}")

# ----------- Health Check -----------
@app.route('/health')
def health_check():
    return jsonify({'status': 'ok'})

# ----------- Run the App -----------
if __name__ == '__main__':
    app.run(debug=True)
