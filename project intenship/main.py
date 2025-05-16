import tkinter as tk
from tkinter import ttk
from datetime import datetime
import time

# SQLAlchemy Imports
from sqlalchemy import create_engine, Column, Integer, String, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# ---------------------------
# SQLAlchemy Base & Model
# ---------------------------
Base = declarative_base()

class SimulationData(Base):
    __tablename__ = 'simulation_data'
    id = Column(Integer, primary_key=True)
    timestamp = Column(String)
    building = Column(Integer)
    floor = Column(Integer)
    unit_status_fb = Column(Float)
    ra_temp = Column(Float)
    ra_humidity = Column(Float)
    sa_temp = Column(Float)
    sa_dpt = Column(Float)
    chws_temp = Column(Float)
    chwr_temp = Column(Float)
    delta_tcw = Column(Float)
    cw_actuator_level = Column(Float)
    cw_actuator_fb = Column(Float)
    fa_temp = Column(Float)
    delta_t_air = Column(Float)
    ra_dft = Column(Float)
    ra_set_temp = Column(Float)
    dh_rh_set = Column(Float)
    unit_status = Column(Float)
    hw_actuator_level = Column(Float)
    hw_actuator_fb = Column(Float)

# ---------------------------
# HVAC Simulator Application
# ---------------------------
class HVACSimulatorApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("HVAC Simulator")
        self.geometry("950x750")
        
        # Simulation context: Building and Floor
        self.building = 1
        self.floor = 1

        # Auto dump settings
        self.auto_dump_interval = None  # seconds between dumps
        self.auto_dump_end_time = None  # timestamp when auto-dump stops
        self.auto_dump_job = None       # reference to the after() job

        # Database sessionmaker (will be set via connect_database)
        self.SessionLocal = None
        self.engine = None
        
        # HVAC parameters with initial values.
        self.params = {
            "Unit Status F/B": 0,
            "RA Temp": 22.0,
            "RA Humidity": 50.0,
            "SA Temp": 22.0,
            "SA DPT": 10.0,
            "CHWS Temp": 6.0,
            "CHWR Temp": 12.0,
            "Delta TCW": 4.0,
            "CW Actuator Level": 50.0,
            "CW Actuator F/B": 0,
            "FA Temp": 22.0,
            "Delta T Air": 2.0,
            "RA DFT": 0.0,
            "RA Set Temp": 22.0,
            "DH %RH Set": 50.0,
            "Unit Status": 1,
            "HW Actuator Level": 50.0,
            "HW Actuator F/B": 0,
        }
        self.param_vars = {}  # holds tkinter DoubleVars for each parameter

        self.create_widgets()
    
    def create_widgets(self):
        # ---------------------------
        # Database Settings Panel
        # ---------------------------
        db_frame = tk.LabelFrame(self, text="Database Settings", padx=10, pady=10)
        db_frame.pack(pady=10, fill="x", padx=10)
        
        # Database Type: OptionMenu
        tk.Label(db_frame, text="DB Type:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.db_type_var = tk.StringVar(value="SQLite")
        db_type_menu = ttk.Combobox(db_frame, textvariable=self.db_type_var, 
                                    values=["SQLite", "PostgreSQL", "MySQL"], state="readonly", width=12)
        db_type_menu.grid(row=0, column=1, padx=5, pady=5)

        # For SQLite, we only need a file path.
        tk.Label(db_frame, text="File/Host:").grid(row=0, column=2, padx=5, pady=5, sticky="w")
        self.db_file_var = tk.StringVar(value="simulation_data.db")
        self.db_file_entry = tk.Entry(db_frame, textvariable=self.db_file_var, width=20)
        self.db_file_entry.grid(row=0, column=3, padx=5, pady=5)
        
        # Additional fields for PostgreSQL/MySQL
        tk.Label(db_frame, text="Port:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.db_port_var = tk.StringVar(value="5432")  # default PostgreSQL port
        self.db_port_entry = tk.Entry(db_frame, textvariable=self.db_port_var, width=10)
        self.db_port_entry.grid(row=1, column=1, padx=5, pady=5)
        
        tk.Label(db_frame, text="Username:").grid(row=1, column=2, padx=5, pady=5, sticky="w")
        self.db_username_var = tk.StringVar(value="postgres")
        self.db_username_entry = tk.Entry(db_frame, textvariable=self.db_username_var, width=15)
        self.db_username_entry.grid(row=1, column=3, padx=5, pady=5)
        
        tk.Label(db_frame, text="Password:").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.db_password_var = tk.StringVar(value="")
        self.db_password_entry = tk.Entry(db_frame, textvariable=self.db_password_var, width=15, show="*")
        self.db_password_entry.grid(row=2, column=1, padx=5, pady=5)
        
        tk.Label(db_frame, text="Database Name:").grid(row=2, column=2, padx=5, pady=5, sticky="w")
        self.db_name_var = tk.StringVar(value="hvac_db")
        self.db_name_entry = tk.Entry(db_frame, textvariable=self.db_name_var, width=15)
        self.db_name_entry.grid(row=2, column=3, padx=5, pady=5)
        
        tk.Button(db_frame, text="Connect Database", command=self.connect_database, bg="lightyellow")\
            .grid(row=3, column=0, columnspan=4, pady=10)
        
        # ---------------------------
        # Top Frame: Building & Floor Controls
        # ---------------------------
        top_frame = tk.Frame(self)
        top_frame.pack(pady=10)
        
        # Building control
        building_frame = tk.Frame(top_frame)
        building_frame.pack(side=tk.LEFT, padx=20)
        tk.Label(building_frame, text="Building").grid(row=0, column=0)
        self.building_label = tk.Label(building_frame, text=str(self.building), width=5, relief="sunken")
        self.building_label.grid(row=0, column=1)
        tk.Button(building_frame, text="+", width=3, command=self.increase_building)\
            .grid(row=0, column=2, padx=2)
        tk.Button(building_frame, text="-", width=3, command=self.decrease_building)\
            .grid(row=0, column=3, padx=2)
        
        # Floor control
        floor_frame = tk.Frame(top_frame)
        floor_frame.pack(side=tk.LEFT, padx=20)
        tk.Label(floor_frame, text="Floor").grid(row=0, column=0)
        self.floor_label = tk.Label(floor_frame, text=str(self.floor), width=5, relief="sunken")
        self.floor_label.grid(row=0, column=1)
        tk.Button(floor_frame, text="+", width=3, command=self.increase_floor)\
            .grid(row=0, column=2, padx=2)
        tk.Button(floor_frame, text="-", width=3, command=self.decrease_floor)\
            .grid(row=0, column=3, padx=2)
        
        # ---------------------------
        # Auto Dump Settings
        # ---------------------------
        auto_dump_frame = tk.Frame(self)
        auto_dump_frame.pack(pady=10)
        
        tk.Label(auto_dump_frame, text="Dump Interval (s):").grid(row=0, column=0, padx=5)
        self.dump_interval_entry = tk.Entry(auto_dump_frame, width=5)
        self.dump_interval_entry.insert(0, "5")  # default 5 seconds
        self.dump_interval_entry.grid(row=0, column=1, padx=5)
        
        tk.Label(auto_dump_frame, text="Total Duration (s):").grid(row=0, column=2, padx=5)
        self.total_duration_entry = tk.Entry(auto_dump_frame, width=5)
        self.total_duration_entry.insert(0, "60")  # default 60 seconds
        self.total_duration_entry.grid(row=0, column=3, padx=5)
        
        tk.Button(auto_dump_frame, text="Start Auto Dump", command=self.start_auto_dump, bg="lightblue")\
            .grid(row=0, column=4, padx=10)
        tk.Button(auto_dump_frame, text="Stop Auto Dump", command=self.stop_auto_dump, bg="lightcoral")\
            .grid(row=0, column=5, padx=10)
        
        # ---------------------------
        # Simulation Parameters Frame
        # ---------------------------
        param_frame = tk.Frame(self)
        param_frame.pack(pady=10, fill=tk.BOTH, expand=True)
        
        # Canvas & Scrollbar for many parameters.
        canvas = tk.Canvas(param_frame)
        scrollbar = tk.Scrollbar(param_frame, orient="vertical", command=canvas.yview)
        self.scrollable_frame = tk.Frame(canvas)
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Create one row per parameter with label, current value, and + / - buttons.
        row = 0
        for param, value in self.params.items():
            tk.Label(self.scrollable_frame, text=param, width=20, anchor="w")\
                .grid(row=row, column=0, padx=5, pady=5)
            var = tk.DoubleVar(value=value)
            self.param_vars[param] = var
            value_label = tk.Label(self.scrollable_frame, textvariable=var, width=10, relief="sunken")
            value_label.grid(row=row, column=1, padx=5)
            tk.Button(self.scrollable_frame, text="+", width=3, 
                      command=lambda p=param: self.increment(p))\
                      .grid(row=row, column=2, padx=5)
            tk.Button(self.scrollable_frame, text="-", width=3, 
                      command=lambda p=param: self.decrement(p))\
                      .grid(row=row, column=3, padx=5)
            row += 1
        
        # ---------------------------
        # Auto Dump Log (Dashboard)
        # ---------------------------
        log_frame = tk.Frame(self)
        log_frame.pack(pady=10, fill=tk.BOTH, expand=True)
        tk.Label(log_frame, text="Auto Dump Log (Dashboard)", font=("Arial", 12, "bold"))\
            .pack()
        self.dump_log = tk.Text(log_frame, height=10)
        self.dump_log.pack(fill=tk.BOTH, expand=True)
    
    # ----- Database Connection -----
    def connect_database(self):
        db_type = self.db_type_var.get()
        if db_type == "SQLite":
            file_path = self.db_file_var.get() or "simulation_data.db"
            connection_string = f"sqlite:///{file_path}"
        elif db_type == "PostgreSQL":
            host = self.db_file_var.get() or "localhost"
            port = self.db_port_var.get() or "5432"
            username = self.db_username_var.get() or "postgres"
            password = self.db_password_var.get() or ""
            dbname = self.db_name_var.get() or "hvac_db"
            connection_string = f"postgresql://{username}:{password}@{host}:{port}/{dbname}"
        elif db_type == "MySQL":
            host = self.db_file_var.get() or "localhost"
            port = self.db_port_var.get() or "3306"
            username = self.db_username_var.get() or "root"
            password = self.db_password_var.get() or ""
            dbname = self.db_name_var.get() or "hvac_db"
            connection_string = f"mysql+pymysql://{username}:{password}@{host}:{port}/{dbname}"
        else:
            connection_string = "sqlite:///simulation_data.db"
        
        try:
            self.engine = create_engine(connection_string, echo=False)
            Base.metadata.create_all(self.engine)
            self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
            self.dump_log.insert(tk.END, f"Connected to database using: {connection_string}\n")
        except Exception as e:
            self.dump_log.insert(tk.END, f"Error connecting to database: {e}\n")
    
    # ----- Building and Floor Controls -----
    def increase_building(self):
        self.building += 1
        self.building_label.config(text=str(self.building))
    
    def decrease_building(self):
        if self.building > 1:
            self.building -= 1
        self.building_label.config(text=str(self.building))
    
    def increase_floor(self):
        self.floor += 1
        self.floor_label.config(text=str(self.floor))
    
    def decrease_floor(self):
        if self.floor > 1:
            self.floor -= 1
        self.floor_label.config(text=str(self.floor))
    
    # ----- Parameter Adjustment -----
    def increment(self, param):
        current = self.param_vars[param].get()
        self.param_vars[param].set(current + 1)
    
    def decrement(self, param):
        current = self.param_vars[param].get()
        self.param_vars[param].set(current - 1)
    
    # ----- Dump Data to Database using SQLAlchemy -----
    def dump_data(self):
        # If not connected, default to SQLite
        if not self.SessionLocal:
            self.engine = create_engine("sqlite:///simulation_data.db", echo=False)
            Base.metadata.create_all(self.engine)
            self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        
        session = self.SessionLocal()
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        data = {param: var.get() for param, var in self.param_vars.items()}
        record = SimulationData(
            timestamp=timestamp,
            building=self.building,
            floor=self.floor,
            unit_status_fb=data["Unit Status F/B"],
            ra_temp=data["RA Temp"],
            ra_humidity=data["RA Humidity"],
            sa_temp=data["SA Temp"],
            sa_dpt=data["SA DPT"],
            chws_temp=data["CHWS Temp"],
            chwr_temp=data["CHWR Temp"],
            delta_tcw=data["Delta TCW"],
            cw_actuator_level=data["CW Actuator Level"],
            cw_actuator_fb=data["CW Actuator F/B"],
            fa_temp=data["FA Temp"],
            delta_t_air=data["Delta T Air"],
            ra_dft=data["RA DFT"],
            ra_set_temp=data["RA Set Temp"],
            dh_rh_set=data["DH %RH Set"],
            unit_status=data["Unit Status"],
            hw_actuator_level=data["HW Actuator Level"],
            hw_actuator_fb=data["HW Actuator F/B"]
        )
        session.add(record)
        session.commit()
        session.close()
        
        log_str = f"{timestamp}: " + ", ".join([f"{p}={data[p]}" for p in data])
        return log_str
    
    # ----- Auto Dump Functions -----
    def start_auto_dump(self):
        try:
            interval = float(self.dump_interval_entry.get())
            total_duration = float(self.total_duration_entry.get())
        except ValueError:
            self.dump_log.insert(tk.END, "Invalid interval or duration input.\n")
            return
        
        self.auto_dump_interval = interval
        self.auto_dump_end_time = time.time() + total_duration
        self.dump_log.insert(tk.END, f"Auto dump started: interval {interval}s, duration {total_duration}s.\n")
        self.auto_dump()  # begin the auto dump cycle
    
    def auto_dump(self):
        current_time = time.time()
        if current_time <= self.auto_dump_end_time:
            log_str = self.dump_data()
            self.dump_log.insert(tk.END, "Auto Dump -> " + log_str + "\n")
            # Schedule next dump after the specified interval
            self.auto_dump_job = self.after(int(self.auto_dump_interval * 1000), self.auto_dump)
        else:
            self.dump_log.insert(tk.END, "Auto dump finished. Total duration reached.\n")
            self.auto_dump_job = None
    
    def stop_auto_dump(self):
        if self.auto_dump_job:
            self.after_cancel(self.auto_dump_job)
            self.auto_dump_job = None
            self.dump_log.insert(tk.END, "Auto dump manually stopped.\n")

# ---------------------------
# Run the Application
# ---------------------------
if __name__ == "__main__":
    app = HVACSimulatorApp()
    app.mainloop()
