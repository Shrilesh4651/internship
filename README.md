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
HVAC-Dashboard/
├── bin/                      # Binary files (if any)
├── build/                    # Compiled files and executables
│   └── app/
├── dist/                     # Distribution files for deployment
├── project-internship/       # Additional project files (if applicable)
├── src/                      # Source code folder
│   ├── app.py                # Main application file
│   ├── application.py        # Core application logic
│   ├── data_generator.py     # Script to generate sensor data
│   ├── gui.py                # GUI implementation (if applicable)
│   ├── main.py               # Entry point script
│   ├── run_app.bat           # Batch file to start the app (Windows)
│   └── main.spec             # Spec file for PyInstaller
├── templates/                # HTML templates for Flask
│   ├── index.html            # Main dashboard page
│   ├── export.html           # Export data page
│   ├── graphical.html        # Graphical data visualization page
│   └── tabular.html          # Tabular data visualization page
├── venv/                     # Virtual environment for Python
├── .vscode/                  # VS Code configuration files
├── .classpath                # Eclipse/IDE specific files
├── .project                  # Eclipse/IDE specific files
├── README.md                 # Project documentation
├── Untitled-1.ts             # TypeScript file (if needed)
├── hvac.db                   # Primary database file
├── simulation_data.db        # Simulation data database
├── export.html               # Export page (duplicate or separate from templates)
├── graphical.html            # Graphical visualization (duplicate or separate)
├── sensor_data.xlsx          # Excel data file
├── sensor_data.db            # Sensor data database
├── simulation_data.pdf       # PDF export of simulation data
├── app.spec                  # Spec file for PyInstaller
├── relay-mimic-simulator/    # Simulator files (if needed)
└── static/                   # Static files (CSS, JS, Images)

```

---

## 🚀 Installation

### Prerequisites:

* Python 3.9+
* Flask
* Plotly
* SQLite

### Steps:

1. **Clone the repository:**

   ```bash
   git clone https://github.com/username/HVAC-Dashboard.git
   cd HVAC-Dashboard
   ```

2. **Create a virtual environment:**

   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

4. **Set environment variables:**

   ```bash
   export FLASK_APP=run.py
   export FLASK_ENV=development
   ```

5. **Run the application:**

   ```bash
   flask run
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

