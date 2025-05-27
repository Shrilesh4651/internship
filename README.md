# HVAC Sensor Data Dashboard

This project is an **HVAC (Heating, Ventilation, and Air Conditioning) Sensor Data Dashboard** that dynamically displays real-time and historical data from multiple sensors. It features data visualization, table views, and various data aggregation options to analyze environmental parameters effectively.

---

## 🌟 Features

* **Dynamic Sensor Data Visualization:** Line and bar charts using Plotly.js.
* **Data Filtering:** By Building, Floor, Sensor Type, Timeline (Raw, Hourly, Daily, Weekly, Monthly, Yearly), and Aggregation (Raw, Min, Max, Avg).
* **Tabular Data View:** Paginated table for sensor data with sorting options.
* **Export Data:** Ability to export data in various formats (Excel, PDF).
* **Responsive Design:** Works seamlessly on both desktop and mobile devices.
* **Real-time Updates:** Auto-refresh every 10 seconds to display the latest data.

---

## 🛠️ Technologies Used

* **Frontend:**

  * HTML, CSS, JavaScript
  * Plotly.js (for interactive charts)
  * Bootstrap (for responsive UI)

* **Backend:**

  * Flask (Python)
  * SQLite (Database)
  * RESTful API (to fetch building, floor, and sensor data)

---

## 📂 Folder Structure

```
project-root/
│
├── bin/                           # Virtual environment binaries
├── build/app/                    # Build artifacts
├── project internship/           # Main simulator application for HVAC
├── src/                          # Source files
│       └── application.py        # Data generator script for simulation
│
├── templates/                    # HTML templates used in the application
│   ├── configure_db.html         # DB configuration page (Updated by Shreedhar - 5 days ago)
│   ├── export.html               # Export data UI (Updated 2 weeks ago)
│   ├── graphical.html            # Graph UI (DB integration changes - 19 hours ago)
│   ├── index.html                # Main dashboard (Updated by Shreedhar - 5 days ago)
│   └── tabular.html              # Table UI for data (Fixed rendering issue)
│
├── venv/                         # Python virtual environment
├── .classpath, .project          # Eclipse project files
├── README.md                     # Project overview and instructions
├── app.py                        # Main Flask app file (DB connection logic updated)
├── app.spec                      # Build specification for packaging
├── application.py                # Simulator application logic
├── data_generator.py             # Generates data for simulation (minor fixes)
└── run_app.bat                   # Batch script to launch the app

```

---

## 🚀 Installation

### Prerequisites:

* Python 3.9+
* Flask
* Plotly
* SQLite

1. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```


2. **Run the application:**

   ```bash
   flask run
   python app.py in terminal
   ```

   The dashboard will be available at: **[http://127.0.0.1:5000/](http://127.0.0.1:5000/)**

---

## 📊 Usage

1. Open the web interface at **[http://127.0.0.1:5000/](http://127.0.0.1:5000/)**.
2. Use the filters on the sidebar to select the building, floor, sensor type, timeline, and aggregation.
3. Click "Update" to refresh the data.
4. Navigate between pages using the pagination buttons.
5. To export data, click on the "Export" button and choose your preferred format.

---

## 📝 API Endpoints

| Endpoint             | Method | Description                          |
| -------------------- | ------ | ------------------------------------ |
| `/buildings`         | GET    | Fetch list of all buildings          |
| `/floors/{building}` | GET    | Fetch floors for a specific building |
| `/sensor-types`      | GET    | Fetch available sensor types         |
| `/tabular-data`      | GET    | Fetch tabular data based on filters  |
| `/export`            | GET    | Export data in Excel or PDF format   |

