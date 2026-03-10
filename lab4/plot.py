import struct
import os
import glob
import sys
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime
import math

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

def plot_multi_temp_profile(pressure_hpa, temp_list, labels, title="Atmospheric Temperature Profile"):
    """Plots Temperature (Y) vs Pressure (X) for multiple sensors."""
    plt.figure(num=title, figsize=(10, 7))
    
    # Standard colors for your sensors
    colors = ['#ff9999', '#ff4d4d', '#cc0000', '#800000', '#0000ff']
    
    for i, temp_data in enumerate(temp_list):
        plt.scatter(pressure_hpa, temp_data, label=labels[i], s=2, alpha=0.6, color=colors[i] if i < len(colors) else None)
    
    plt.title(title)
    plt.xlabel("Pressure (hPa)")
    plt.ylabel("Temperature (°C)")
    
    # Pressure usually drops from left to right in atmospheric plots
    # plt.gca().invert_xaxis() 
    
    plt.legend(loc='best', markerscale=5)
    plt.grid(True, linestyle='--', alpha=0.5)
    plt.tight_layout()

    filename = title.replace(" ", "_") + ".png"
    plt.savefig(os.path.join("graphs", filename))
    print(f"Saved: graphs/{filename}")

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
        
        mode = "FLIGHT"
        time_data = mission_data['time']

        # 1. Temperatures (5 System + 1 BME)
        # Note: BME Temp is index 2 in your parsing logic
        all_temps = mission_data['temps'] + [mission_data['bme'][0]]
        temp_labels = ["T-EXT-BACK", "T-EXT-FRONT", "T-BATTERY", "T-CPU", "T-INTERNAL/BME"]
        temp_colors = ['#ff9999', '#ff4d4d', '#cc0000', '#800000', '#4d0000', '#0000ff']
        create_window(f"Temperatures {mode}", time_data, all_temps, temp_labels, "°C", color_map=temp_colors)

        # Temp versus Pressure Overlay
        pressure_data = [mission_data['bme'][1]]  # BME Pressure
        plot_multi_temp_profile(pressure_data, all_temps, temp_labels, "Temperature vs Pressure Profile")

        # 2. Accelerometer
        create_window(f"Accelerometer", time_data, mission_data['accel'], ['X', 'Y', 'Z'], "m/s² OR g's")

        # 3. Gyroscope
        create_window(f"Gyroscope", time_data, mission_data['gyro'], ['X', 'Y', 'Z'], "deg/s")

        # 4. Magnetometer
        create_window(f"Magnetometer", time_data, mission_data['mag'], ['X', 'Y', 'Z'], "μT")

        # 5. BME Pressure
        create_window(f"BME280 Pressure", time_data, [mission_data['bme'][1]], ["Pressure"], "hPa")

        # 6. BME Humidity
        create_window(f"BME280 Humidity", time_data, [mission_data['bme'][2]], ["Humidity"], "%")

        # 7. INA Current
        A = [c / -1000.0 for c in mission_data['ina'][1]]
        create_window(f"INA219 Current", time_data, [A], ["Current"], "A")

        # 8. INA Power
        W = [p / 1000.0 for p in mission_data['ina'][2]]
        create_window(f"INA219 Power", time_data, [W], ["Power"], "W")
        
        # 9. Bus Voltage (Calculated from 12V rail - Shunt Voltage)
        # Assuming d[18] (ina[0]) is Shunt Voltage in mV
        V = mission_data['ina'][0]
        create_window(f"INA219 Bus Voltage", time_data, [V], ["Voltage"], "V")

        # GPS
        create_window(f"GPS Latitude", time_data, [mission_data['gps'][0]], ["Latitude"], "Degrees")
        create_window(f"GPS Longitude", time_data, [mission_data['gps'][1]], ["Longitude"], "Degrees")
        
        # Overlaying GPS (index 2 of gps data) and MPL altitude'
        def hpa_to_altitude(pressure_hpa):
            # Constants for the Standard Atmosphere
            P0 = 1013.25 # Sea level pressure in hPa
            
            # If pressure is very low (Stratosphere), we use a different calculation
            # 226.32 hPa is the approximate pressure at the Tropopause (11km)
            if pressure_hpa > 226.32:
                # Troposphere Math
                altitude = 44330.77 * (1.0 - (pressure_hpa / P0)**0.190263)
            else:
                # Stratosphere Math (11km to 20km+)
                # This accounts for the isothermal layer where temp is constant (-56.5C)
                h_tropo = 11000  # Tropopause height in meters
                p_tropo = 226.32 # Pressure at tropopause
                T_tropo = 216.65 # Temp in Kelvin (-56.5C)
                R = 287.058      # Gas constant
                g = 9.80665      # Gravity
                
                altitude = h_tropo - (R * T_tropo / g) * math.log(pressure_hpa / p_tropo)

            return altitude
        B = [hpa_to_altitude(p) for p in mission_data['bme'][1]]
        M = [m/3.28084 for m in mission_data["mpl"]]  
        alt_data = [mission_data['gps'][2], M, B]
        alt_labels = ["GPS Altitude", "MPL Altitude", "BME280 Altitude"]
        create_window("Altitude Overlay", time_data, alt_data, alt_labels, "Altitude (m)")

        # statuses
        create_window(f"Subsystem Statuses", time_data, mission_data['statuses'], ['BME280', 'INA219', 'IMU', 'Temp', 'MPL', 'GPS', 'RTC'], "Status (0=Fail, 1=OK)") 
        
        generate_html_gallery("graphs")
        
        plt.show()

        
    else:
        print(f"No data found in {target_folder} matching those filters.")
