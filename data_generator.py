import sqlite3
import random
from datetime import datetime
import time
import threading

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

if __name__ == '__main__':
    init_db()
    thread = threading.Thread(target=continuous_update, daemon=True)
    thread.start()
    print("Data generation started. Press Ctrl+C to stop.")
    while True:
        time.sleep(1)
