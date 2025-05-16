import tkinter as tk
import requests
import asyncio
import websockets
import threading
import json

SERVER_URL = "http://localhost:8000"
WS_URL = "ws://localhost:8000/ws"

class HVACSimulator:
    def __init__(self, root):
        self.root = root
        self.root.title("HVAC Simulator")
        
        self.parameter_label = tk.Label(root, text="Parameter Name")
        self.parameter_label.pack()
        
        self.parameter_entry = tk.Entry(root)
        self.parameter_entry.pack()
        
        self.value_label = tk.Label(root, text="Value")
        self.value_label.pack()
        
        self.value_entry = tk.Entry(root)
        self.value_entry.pack()
        
        self.send_button = tk.Button(root, text="Send", command=self.send_data)
        self.send_button.pack()

        self.realtime_label = tk.Label(root, text="Real-time Updates", font=("Arial", 14))
        self.realtime_label.pack()

        self.updates_text = tk.Text(root, height=10, width=40)
        self.updates_text.pack()

        # Start WebSocket listener
        threading.Thread(target=self.start_websocket, daemon=True).start()

    def send_data(self):
        parameter = self.parameter_entry.get()
        value = float(self.value_entry.get())

        data = {"unit_id": "Unit1", "parameter_name": parameter, "value": value}
        response = requests.post(f"{SERVER_URL}/store", json=data)

        if response.status_code == 200:
            self.updates_text.insert(tk.END, f"Sent: {parameter} = {value}\n")
        else:
            self.updates_text.insert(tk.END, "Failed to send data\n")

    def start_websocket(self):
        asyncio.run(self.listen_websocket())

    async def listen_websocket(self):
        async with websockets.connect(WS_URL) as websocket:
            while True:
                message = await websocket.recv()
                data = json.loads(message)
                self.updates_text.insert(tk.END, f"Updated: {data['parameter']} = {data['value']}\n")

if __name__ == "__main__":
    root = tk.Tk()
    app = HVACSimulator(root)
    root.mainloop()
