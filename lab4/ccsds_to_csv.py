import struct
import os
import glob
import sys
import csv
from datetime import datetime

# 1. Configuration - UPDATED TO MATCH DEBUGGER REF
PAYLOAD_FORMAT = ">Iffff fff fff fff fff fff f fff BBBBBBB"
HEADER_SIZE = 6
EXPORT_DIR = "csv_exports"

def parse_date_arg(date_str):
    try:
        dt = datetime.strptime(date_str, "%m/%d/%Y|%H:%M:%S")
        return dt.timestamp()
    except Exception as e:
        print(f"Error parsing date '{date_str}': {e}")
        sys.exit(1)

def export_to_csv(folder_path, min_ts=None, max_ts=None):
    if not os.path.exists(EXPORT_DIR):
        os.makedirs(EXPORT_DIR)

    # 1. Sort files by modification time so rotation order is preserved
    files = glob.glob(os.path.join(folder_path, "*.ccsds"))
    files.sort(key=os.path.getmtime) 

    if not files:
        print(f"No data found in {folder_path}")
        return

    timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_filename = os.path.join(EXPORT_DIR, f"flight_data_{timestamp_str}.csv")

    header_cols = [
        'Estimated-Unix-Timestamp', 'Iso-Time',
        'Temp-Back-C', 'Temp-Front-C', 'Temp-Batt-C', 'Temp-CPU-C',
        'Accel-X-g', 'Accel-Y-g', 'Accel-Z-g',
        'Gyro-X-dps', 'Gyro-Y-dps', 'Gyro-Z-dps',
        'Mag-X-uT', 'Mag-Y-uT', 'Mag-Z-uT',
        'BME-Temp-C', 'BME-Pres-hPa', 'BME-Hum',
        'Volt-V', 'Curr-A', 'Power-W',
        'MPL-Alt-ft', 'Lat', 'Lon', 'GPS-Alt-m',
        'Stat-BME', 'Stat-INA', 'Stat-IMU', 
        'Stat-Temp', 'Stat-MPL', 'Stat-GPS', 
        'Stat-RTC'
    ]

    count = 0
    with open(output_filename, mode='w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(header_cols)

        for filepath in files:
            print(f"Processing: {os.path.basename(filepath)}")
            with open(filepath, "rb") as f:
                while True:
                    header_data = f.read(6)
                    if len(header_data) < 6: break

                    h = struct.unpack(">HHH", header_data)
                    length = h[2] + 1
                    payload = f.read(length)
                    if len(payload) < length: break

                    try:
                        d = struct.unpack(PAYLOAD_FORMAT, payload)
                        ts = d[0]
                        amps = d[18] / -1000   # Converts -mA to A (result: 0.242)
                        watts = d[19] / 1000  # Converts mW to W (result: 3.19)
                        # Date Filtering
                        if min_ts and ts < min_ts: continue
                        if max_ts and ts > max_ts: continue

                        iso_time = datetime.fromtimestamp(ts).isoformat()

                        # Construct Row based on your state machine's pack order:
                        row = [ts, iso_time] + list(d[1:18]) + [amps, watts] + list(d[20:])
                        
                        writer.writerow(row)
                        count += 1
                    except struct.error:
                        continue
    
    print(f"Success: {count} rows saved to '{output_filename}'")

if __name__ == "__main__":
    is_sim = "--simulate" in sys.argv
    target_folder = "simulated-data" if is_sim else "data"
    
    min_ts, max_ts = None, None
    for arg in sys.argv:
        if arg.startswith("--minDate="):
            min_ts = parse_date_arg(arg.split("=")[1])
        if arg.startswith("--maxDate="):
            max_ts = parse_date_arg(arg.split("=")[1])

    export_to_csv(target_folder, min_ts, max_ts)
