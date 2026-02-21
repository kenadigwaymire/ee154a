import struct
import os
import glob
import sys
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime

# 1. Configuration
# ts, 5 temps, 3 accel, 3 gyro, 3 mag, 3 bme, 3 ina, is_utc, bme280_status, ina219_status, imu_status, temp_status
PAYLOAD_FORMAT = ">Iffff fff fff fff fff fff fff f BBBBBBB"
HEADER_SIZE = 6

def parse_date_arg(date_str):
    """Converts 'MM/DD/YYYY|HH:MM:SS' string into a Unix timestamp."""
    try:
        dt = datetime.strptime(date_str, "%m/%d/%Y|%H:%M:%S")
        return dt.timestamp()
    except Exception as e:
        print(f"Error parsing date '{date_str}': {e}")
        print("Required Format: \"MM/DD/YYYY|HH:MM:%S\" (Use Quotes!)")
        sys.exit(1)

def read_mission_data_filtered(folder_path, min_ts=None, max_ts=None):
    """Parses .ccsds files and filters data by timestamp range."""
    data = {
        'time': [],
        'temps': [[] for _ in range(4)],
        'accel': [[] for _ in range(3)],
        'gyro':  [[] for _ in range(3)],
        'mag':   [[] for _ in range(3)],
        'bme':   [[] for _ in range(3)],   # [pressure_hPa, humidity_pct, temp_C] (per your bme280.get_data())
        'ina':   [[] for _ in range(3)],   # [voltage, current, power] (per your ina219.read_data())
        'mpl':   [],                     # Assuming mpl data is a single value (e.g., pressure)
        'gps':   [[] for _ in range(3)],                     # Assuming gps data is a single value (e.g., altitude)
        'statuses': [[] for _ in range(7)]  # [bme280_status, ina219_status, imu_status, temp_status, mpl_status, gps_status, rtc_status]

    }

    files = sorted(glob.glob(os.path.join(folder_path, "*.ccsds")))
    if not files:
        print(f"No data found in {folder_path}")
        return None

    for filepath in files:
        with open(filepath, "rb") as f:
            while True:
                header_data = f.read(HEADER_SIZE)
                if len(header_data) < HEADER_SIZE:
                    break

                header = struct.unpack(">HHH", header_data)
                length = header[2] + 1
                payload = f.read(length)
                if len(payload) < length:
                    break

                try:
                    d = struct.unpack(PAYLOAD_FORMAT, payload)
                    ts = d[0]

                    # Filter Logic
                    if min_ts is not None and ts < min_ts:
                        continue
                    if max_ts is not None and ts > max_ts:
                        continue

                    data['time'].append(ts)
                    # 4 Temps: Indices 1-4
                    for i in range(4): data['temps'][i].append(d[1+i])
                    # IMU/BME/INA/MPL/GPS (Groups of 3)
                    for i in range(3): data['accel'][i].append(d[5+i])
                    for i in range(3): data['gyro'][i].append(d[8+i])
                    for i in range(3): data['mag'][i].append(d[11+i])
                    for i in range(3): data['bme'][i].append(d[14+i])
                    for i in range(3): data['ina'][i].append(d[17+i])
                    data['mpl'].append(d[20])
                    for i in range(3): data['gps'][i].append(d[21+i])
                    # Statuses: Indices 26-32
                    for i in range(7): data['statuses'][i].append(d[24+i])

                except struct.error:
                    continue

    return data

def create_window(title, x_timestamps, y_data_list, labels, y_label, color_map=None):
    """Generates a window using scatter plots and saves it to the graphs folder."""
    plt.figure(num=title, figsize=(10, 6))
    dates = [datetime.fromtimestamp(ts) for ts in x_timestamps]

    for i, y_data in enumerate(y_data_list):
        color = color_map[i] if color_map else None
        plt.scatter(dates, y_data, label=labels[i], s=3, alpha=0.7, color=color)

    ax = plt.gca()
    locator = mdates.AutoDateLocator()
    formatter = mdates.ConciseDateFormatter(locator)
    ax.xaxis.set_major_locator(locator)
    ax.xaxis.set_major_formatter(formatter)

    plt.title(title)
    plt.xlabel("Time (UTC)")
    plt.ylabel(y_label)
    plt.legend(loc='upper right', markerscale=3)
    plt.grid(True, linestyle=':', alpha=0.4)
    plt.gcf().autofmt_xdate()
    plt.tight_layout()

    # --- SAVE LOGIC ---
    # Sanitize title to create a valid filename
    filename = title.replace(" ", "_").replace("(", "").replace(")", "").replace("/", "-") + ".png"
    save_path = os.path.join("graphs", filename)
    plt.savefig(save_path)
    print(f"Saved: {save_path}")
    
def generate_html_gallery(folder="graphs"):
    """Creates a simple index.html to view all generated plots."""
    files = sorted(glob.glob(os.path.join(folder, "*.png")))
    html_content = """
    <html>
    <head>
        <title>Mission Data Plots</title>
        <style>
            body { font-family: sans-serif; background: #f0f0f0; text-align: center; }
            .graph-container { margin: 20px auto; padding: 10px; background: white; 
                               border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); display: inline-block; }
            img { max-width: 90vw; height: auto; }
            h1 { color: #333; }
        </style>
    </head>
    <body>
        <h1>Mission Control - Real Time Graphs</h1>
    """
    
    for f in files:
        rel_path = os.path.basename(f)
        html_content += f'<div class="graph-container"><h3>{rel_path}</h3>'
        html_content += f'<img src="{rel_path}"></div><br>\n'
    
    html_content += "</body></html>"
    
    with open(os.path.join(folder, "index.html"), "w") as f:
        f.write(html_content)
    print(f"Webpage updated: {os.path.join(folder, 'index.html')}")

if __name__ == "__main__":
    target_folder = "data"
    
    # Ensure the graphs directory exists
    if not os.path.exists("graphs"):
        os.makedirs("graphs")

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
        
<<<<<<< HEAD
        all_temps = mission_data['temps'] + [mission_data['bme'][0]]
        temp_labels = [f'T{i+1}' for i in range(4)] + ['BME Temp']
        temp_colors = ['#ff9999', '#ff4d4d', '#cc0000', '#800000', '#4d0000', '#0000ff']
        create_window(f"Temperatures", time_data, all_temps, temp_labels, "°C", color_map=temp_colors)
=======
        mode = "FLIGHT"
        time_data = mission_data['time']

        # 1. Temperatures (5 System + 1 BME)
        # Note: BME Temp is index 2 in your parsing logic
        all_temps = mission_data['temps'] + [mission_data['bme'][0]]
        temp_labels = [f'T{i+1}' for i in range(4)] + ['BME Temp']
        temp_colors = ['#ff9999', '#ff4d4d', '#cc0000', '#800000', '#4d0000', '#0000ff']
        create_window(f"Temperatures {mode}", time_data, all_temps, temp_labels, "°C", color_map=temp_colors)

        # 2. Accelerometer
        create_window(f"Accelerometer {mode}", time_data, mission_data['accel'], ['X', 'Y', 'Z'], "m/s² OR g")

        # 3. Gyroscope
        create_window(f"Gyroscope {mode}", time_data, mission_data['gyro'], ['X', 'Y', 'Z'], "rad/s")

        # 4. Magnetometer
        create_window(f"Magnetometer {mode}", time_data, mission_data['mag'], ['X', 'Y', 'Z'], "μT")

        # 5. BME Pressure
        create_window(f"BME280 Pressure {mode}", time_data, [mission_data['bme'][1]], ["Pressure"], "hPa")

        # 6. BME Humidity
        create_window(f"BME280 Humidity {mode}", time_data, [mission_data['bme'][2]], ["Humidity"], "%")

        # 7. INA Current
        A = [c / 1000.0 for c in mission_data['ina'][0]]
        create_window(f"INA219 Current {mode}", time_data, [A], ["Current"], "A")

        # 8. INA Power
        W = [p / 1000.0 for p in mission_data['ina'][1]]
        create_window(f"INA219 Power {mode}", time_data, [W], ["Power"], "W")
        
        # 9. Bus Voltage (Calculated from 12V rail - Shunt Voltage)
        # Assuming d[18] (ina[0]) is Shunt Voltage in mV
        V = [(12000 - v) / 1000.0 for v in mission_data['ina'][2]]
        create_window(f"Bus Voltage {mode}", time_data, [V], ["Voltage"], "V")

        # GPS
        create_window(f"GPS Latitude {mode}", time_data, [mission_data['gps'][0]], ["Latitude"], "Degrees")
        create_window(f"GPS Longitude {mode}", time_data, [mission_data['gps'][1]], ["Longitude"], "Degrees")
        create_window(f"GPS Altitude {mode}", time_data, [mission_data['gps'][2]], ["Altitude"], "m")

        # mpl
        create_window(f"MPL Pressure {mode}", time_data, [mission_data['mpl']], ["Pressure"], "hPa")

        # statuses
        create_window(f"Subsystem Statuses {mode}", time_data, mission_data['statuses'], ['BME280', 'INA219', 'IMU', 'Temp', 'MPL', 'GPS', 'RTC'], "Status (0=Fail, 1=OK)") 
>>>>>>> bc0825691bc895415c220f4a276aeb299cdb286f

        # 2. Accelerometer
        create_window(f"Accelerometer", time_data, mission_data['accel'], ['X', 'Y', 'Z'], "m/s² OR g")

        # 3. Gyroscope
        create_window(f"Gyroscope", time_data, mission_data['gyro'], ['X', 'Y', 'Z'], "rad/s")

        # 4. Magnetometer
        create_window(f"Magnetometer", time_data, mission_data['mag'], ['X', 'Y', 'Z'], "μT")

        # 5. BME Pressure
        create_window(f"BME280 Pressure", time_data, [mission_data['bme'][1]], ["Pressure"], "hPa")

        # 6. BME Humidity
        create_window(f"BME280 Humidity", time_data, [mission_data['bme'][2]], ["Humidity"], "%")

        # 7. INA Current
        A = [c / 1000.0 for c in mission_data['ina'][0]]
        create_window(f"INA219 Current", time_data, [A], ["Current"], "A")

        # 8. INA Power
        W = [p / 1000.0 for p in mission_data['ina'][1]]
        create_window(f"INA219 Power", time_data, [W], ["Power"], "W")
        
        # 9. Bus Voltage (Calculated from 12V rail - Shunt Voltage)
        # Assuming d[18] (ina[0]) is Shunt Voltage in mV
        V = [v / 1000.0 for v in mission_data['ina'][2]]
        create_window(f"Bus Voltage", time_data, [V], ["Voltage"], "V")

        # GPS
        create_window(f"GPS Latitude", time_data, [mission_data['gps'][0]], ["Latitude"], "Degrees")
        create_window(f"GPS Longitude", time_data, [mission_data['gps'][1]], ["Longitude"], "Degrees")
        create_window(f"GPS Altitude", time_data, [mission_data['gps'][2]], ["Altitude"], "m")

        # mpl
        create_window(f"MPL Pressure", time_data, [mission_data['mpl']], ["Pressure"], "hPa")

        # statuses
        create_window(f"Subsystem Statuses", time_data, mission_data['statuses'], ['BME280', 'INA219', 'IMU', 'Temp', 'MPL', 'GPS', 'RTC'], "Status (0=Fail, 1=OK)") 
        generate_html_gallery("graphs")
        
        plt.show()

        
    else:
        print(f"No data found in {target_folder} matching those filters.")