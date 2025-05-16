import sqlite3
import random
from datetime import datetime, timedelta
import time

def create_database():
    """Create the database and the sensor_data table."""
    with sqlite3.connect('sensor_data.db') as conn:
        cursor = conn.cursor()
        cursor.execute(''' 
            CREATE TABLE IF NOT EXISTS sensor_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                building_id TEXT,
                floor_number INTEGER,
                sensor_type TEXT,
                timestamp TEXT,
                value REAL,
                status TEXT,
                fan_status TEXT,
                rotor_status TEXT,
                pipe_status TEXT,
                fan_id TEXT
            );
        ''')
        conn.commit()

def generate_sample_data():
    """Generate sample sensor data every second."""
    # Sample buildings, floors, and sensor types
    buildings = ['Building 1', 'Building 2', 'Building 3']
    floors = [1, 2, 3, 4]
    sensor_types = ['temperature', 'humidity', 'pressure', 'digital']

    # Open the connection once and use it throughout
    with sqlite3.connect('sensor_data.db') as conn:
        cursor = conn.cursor()
        while True:
            # Get the current timestamp (current time for each entry)
            current_timestamp = datetime.now()

            # For each cycle, generate a sample row for each building, floor, and sensor type
            for building in buildings:
                for floor in floors:
                    for sensor_type in sensor_types:
                        # Generate sample value based on sensor type
                        if sensor_type == 'temperature':
                            value = random.uniform(15.0, 30.0)  # °C
                        elif sensor_type == 'humidity':
                            value = random.uniform(40.0, 60.0)  # %
                        elif sensor_type == 'pressure':
                            value = random.uniform(990.0, 1020.0)  # hPa
                        elif sensor_type == 'digital':
                            value = random.choice([0, 1])  # Digital flag as numeric value
                        else:
                            value = None

                        # For digital sensors, set status and fan_id; for non-digital, leave as None
                        status = random.choice(['ON', 'OFF']) if sensor_type == 'digital' else None
                        fan_status = random.choice(['ON', 'OFF'])
                        rotor_status = random.choice(['ON', 'OFF'])
                        pipe_status = random.choice(['ON', 'OFF'])
                        fan_id = random.choice([None, 'Fan A', 'Fan B', 'Fan C']) if sensor_type == 'digital' else None

                        # Insert the sample row into sensor_data table
                        cursor.execute('''
                            INSERT INTO sensor_data 
                            (building_id, floor_number, sensor_type, timestamp, value, status, fan_status, rotor_status, pipe_status, fan_id)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (
                            building,
                            floor,
                            sensor_type,
                            current_timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                            value,
                            status,
                            fan_status,
                            rotor_status,
                            pipe_status,
                            fan_id
                        ))
            # Commit the data after each cycle
            conn.commit()

            # Sleep for 1 second before generating the next set of data
            time.sleep(1)

if __name__ == '__main__':
    create_database()        # Create the database and table
    generate_sample_data()   # Continuously generate and insert sample data every second
    print("Database and sample data generation started...")
