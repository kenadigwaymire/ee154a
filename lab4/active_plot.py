import struct
import os
import glob
import sys
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.animation import FuncAnimation
from datetime import datetime

# 1. Configuration
PAYLOAD_FORMAT = ">Ifffff fff fff fff B"
HEADER_SIZE = 6 

class LiveMissionPlotter:
    def __init__(self, folder_path, min_ts=None, max_ts=None):
        self.folder_path = folder_path
        self.min_ts = min_ts
        self.max_ts = max_ts
        
        # Data storage
        self.data = {
            'time': [], 'temps': [[] for _ in range(5)],
            'accel': [[] for _ in range(3)], 'gyro': [[] for _ in range(3)],
            'mag': [[] for _ in range(3)]
        }

        # Setup Figure and Subplots (Multi-window live update is tricky, 
        # so we use 4 subplots in one large dashboard for performance)
        self.fig, self.axes = plt.subplots(4, 1, figsize=(12, 10), sharex=True)
        self.fig.canvas.manager.set_window_title(f"LIVE Telemetry: {self.folder_path}")
        
        # Color palettes
        self.temp_colors = ["#00a018", '#ff4d4d', "#0029cc", "#D000C2", "#000000"]
        self.imu_colors = ['#1f77b4', '#ff7f0e', '#2ca02c'] # Blue, Orange, Green

    def read_new_data(self):
        """Re-scans files and extracts data within the time window."""
        # Reset data for a clean full-scan (ensures no duplicates)
        new_data = {
            'time': [], 'temps': [[] for _ in range(5)],
            'accel': [[] for _ in range(3)], 'gyro': [[] for _ in range(3)],
            'mag': [[] for _ in range(3)]
        }

        files = sorted(glob.glob(os.path.join(self.folder_path, "*.ccsds")))
        for filepath in files:
            with open(filepath, "rb") as f:
                while True:
                    header_data = f.read(HEADER_SIZE)
                    if len(header_data) < HEADER_SIZE: break
                    header = struct.unpack(">HHH", header_data)
                    length = header[2] + 1
                    payload = f.read(length)
                    if len(payload) < length: break
                    try:
                        d = struct.unpack(PAYLOAD_FORMAT, payload)
                        ts = d[0]
                        if self.min_ts and ts < self.min_ts: continue
                        if self.max_ts and ts > self.max_ts: continue

                        new_data['time'].append(datetime.fromtimestamp(ts))
                        for i in range(5): new_data['temps'][i].append(d[1+i])
                        for i in range(3): new_data['accel'][i].append(d[6+i])
                        for i in range(3): new_data['gyro'][i].append(d[9+i])
                        for i in range(3): new_data['mag'][i].append(d[12+i])
                    except struct.error: continue
        self.data = new_data

    def update_plots(self, frame):
        """The animation loop called every 10 seconds."""
        self.read_new_data()
        
        if not self.data['time']:
            return

        # Clear axes for refresh
        for ax in self.axes:
            ax.clear()
            ax.grid(True, linestyle=':', alpha=0.4)

        # 1. Accel
        for i, label in enumerate(['Ax', 'Ay', 'Az']):
            self.axes[0].scatter(self.data['time'], self.data['accel'][i], s=3, label=label, color=self.imu_colors[i])
        self.axes[0].set_ylabel("Accel (m/s²)")
        
        # 2. Gyro
        for i, label in enumerate(['Gx', 'Gy', 'Gz']):
            self.axes[1].scatter(self.data['time'], self.data['gyro'][i], s=3, label=label, color=self.imu_colors[i])
        self.axes[1].set_ylabel("Gyro (rad/s)")

        # 3. Mag
        for i, label in enumerate(['Mx', 'My', 'Mz']):
            self.axes[2].scatter(self.data['time'], self.data['mag'][i], s=3, label=label, color=self.imu_colors[i])
        self.axes[2].set_ylabel("Mag (μT)")

        # 4. Temps
        for i in range(5):
            self.axes[3].scatter(self.data['time'], self.data['temps'][i], s=3, label=f'T{i+1}', color=self.temp_colors[i])
        self.axes[3].set_ylabel("Temp (°C)")

        # Formatting
        locator = mdates.AutoDateLocator()
        formatter = mdates.ConciseDateFormatter(locator)
        self.axes[3].xaxis.set_major_locator(locator)
        self.axes[3].xaxis.set_major_formatter(formatter)
        
        for ax in self.axes:
            ax.legend(loc='upper right', markerscale=3, fontsize='small')

        plt.tight_layout()
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Dashboard Updated. Points: {len(self.data['time'])}")

def parse_date_arg(date_str):
    try:
        return datetime.strptime(date_str, "%m/%d/%Y|%H:%M:%S").timestamp()
    except:
        print("Format Error. Use: \"MM/DD/YYYY|HH:MM:SS\"")
        sys.exit(1)

if __name__ == "__main__":
    is_sim = "--simulate" in sys.argv
    folder = "simulated-data" if is_sim else "data"
    
    min_t, max_t = None, None
    for arg in sys.argv:
        if arg.startswith("--minDate="): min_t = parse_date_arg(arg.split("=")[1])
        if arg.startswith("--maxDate="): max_t = parse_date_arg(arg.split("=")[1])

    try:
        plotter = LiveMissionPlotter(folder, min_t, max_t)
        
        # interval=10000 means 10,000 milliseconds (10 seconds)
        ani = FuncAnimation(plotter.fig, plotter.update_plots, interval=10000, cache_frame_data=False)
        
        print("Live Plotter Active. Press Ctrl+C in this terminal to stop.")
        plt.show()

    except KeyboardInterrupt:
        print("\n[STOPPING] Keyboard interrupt detected. Closing plotter...")
        plt.close('all')  # Force close all matplotlib windows
        sys.exit(0)