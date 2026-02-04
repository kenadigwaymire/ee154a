import struct
import os
import glob
import sys
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime

# 1. Configuration
PAYLOAD_FORMAT = ">Ifffff fff fff fff B"
HEADER_SIZE = 6 

def parse_date_arg(date_str):
    """Converts 'MM/DD/YYYY|HH:MM:SS' string into a Unix timestamp."""
    try:
        dt = datetime.strptime(date_str, "%m/%d/%Y|%H:%M:%S")
        return dt.timestamp()
    except Exception as e:
        print(f"Error parsing date '{date_str}': {e}")
        print("Required Format: \"MM/DD/YYYY|HH:MM:SS\" (Use Quotes!)")
        sys.exit(1)

def read_mission_data_filtered(folder_path, min_ts=None, max_ts=None):
    """Parses .ccsds files and filters data by timestamp range."""
    data = {
        'time': [], 'temps': [[] for _ in range(5)],
        'accel': [[] for _ in range(3)], 'gyro': [[] for _ in range(3)],
        'mag': [[] for _ in range(3)]
    }

    files = sorted(glob.glob(os.path.join(folder_path, "*.ccsds")))
    if not files:
        print(f"No data found in {folder_path}")
        return None

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

                    # Filter Logic
                    if min_ts and ts < min_ts: continue
                    if max_ts and ts > max_ts: continue

                    data['time'].append(ts)
                    for i in range(5): data['temps'][i].append(d[1+i])
                    for i in range(3): data['accel'][i].append(d[6+i])
                    for i in range(3): data['gyro'][i].append(d[9+i])
                    for i in range(3): data['mag'][i].append(d[12+i])
                except struct.error: continue
                
    return data

def create_window(title, x_timestamps, y_data_list, labels, y_label, color_map=None):
    """Generates a window using scatter plots for all data points."""
    plt.figure(num=title, figsize=(10, 6))
    dates = [datetime.fromtimestamp(ts) for ts in x_timestamps]
    
    for i, y_data in enumerate(y_data_list):
        color = color_map[i] if color_map else None
        # Using s=3 for smaller, sharper points
        plt.scatter(dates, y_data, label=labels[i], s=3, alpha=0.7, color=color)
    
    ax = plt.gca()
    locator = mdates.AutoDateLocator()
    formatter = mdates.ConciseDateFormatter(locator)
    ax.xaxis.set_major_locator(locator)
    ax.xaxis.set_major_formatter(formatter)
    
    plt.title(title)
    plt.xlabel("Time (UTC)")
    plt.ylabel(y_label)
    plt.legend(loc='upper right', markerscale=3) # Scale up legend markers for visibility
    plt.grid(True, linestyle=':', alpha=0.4)
    plt.gcf().autofmt_xdate()
    plt.tight_layout()

if __name__ == "__main__":
    is_sim = "--simulate" in sys.argv
    target_folder = "simulated-data" if is_sim else "data"
    
    min_ts, max_ts = None, None
    for arg in sys.argv:
        if arg.startswith("--minDate="):
            min_ts = parse_date_arg(arg.split("=")[1])
        if arg.startswith("--maxDate="):
            max_ts = parse_date_arg(arg.split("=")[1])

    mission_data = read_mission_data_filtered(target_folder, min_ts, max_ts)
    
    if mission_data and mission_data['time']:
        start_utc = datetime.fromtimestamp(mission_data['time'][0])
        end_utc = datetime.fromtimestamp(mission_data['time'][-1])
        print(f"Plotting {len(mission_data['time'])} points.")
        print(f"Range: {start_utc} to {end_utc}")

        mode = "SIMULATION" if is_sim else "FLIGHT"
        
        # Window 1: Accelerometer
        create_window(f"Accelerometer ({mode})", mission_data['time'], 
                      mission_data['accel'], ['X', 'Y', 'Z'], "m/s²")

        # Window 2: Gyroscope
        create_window(f"Gyroscope ({mode})", mission_data['time'], 
                      mission_data['gyro'], ['X', 'Y', 'Z'], "rad/s")

        # Window 3: Magnetometer
        create_window(f"Magnetometer ({mode})", mission_data['time'], 
                      mission_data['mag'], ['X', 'Y', 'Z'], "μT")

        # Window 4: Temperatures
        temp_colors = ['#ff9999', '#ff4d4d', '#cc0000', '#800000', '#4d0000']
        create_window(f"Temperatures ({mode})", mission_data['time'], 
                      mission_data['temps'], [f'T{i+1}' for i in range(5)], "°C", 
                      color_map=temp_colors)
        
        plt.show()
    else:
        print(f"No data found in {target_folder} matching those filters.")