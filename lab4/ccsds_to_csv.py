import struct
import os
import glob
import sys
import csv
from datetime import datetime

# 1. Configuration
PAYLOAD_FORMAT = ">Ifffff fff fff fff fff fff B"
HEADER_SIZE = 6
EXPORT_DIR = "csv_exports"  # Target folder

def parse_date_arg(date_str):
    """Converts 'MM/DD/YYYY|HH:MM:SS' string into a Unix timestamp."""
    try:
        dt = datetime.strptime(date_str, "%m/%d/%Y|%H:%M:%S")
        return dt.timestamp()
    except Exception as e:
        print(f"Error parsing date '{date_str}': {e}")
        print("Required Format: \"MM/DD/YYYY|HH:MM:SS\" (Use Quotes!)")
        sys.exit(1)

def export_to_csv(folder_path, min_ts=None, max_ts=None):
    """Parses .ccsds files and writes filtered data to the exports folder."""
    
    # Ensure the export directory exists
    if not os.path.exists(EXPORT_DIR):
        os.makedirs(EXPORT_DIR)
        print(f"Created directory: {EXPORT_DIR}")

    files = sorted(glob.glob(os.path.join(folder_path, "*.ccsds")))
    if not files:
        print(f"No data found in {folder_path}")
        return

    # Generate filename based on current time to avoid overwriting
    timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_filename = os.path.join(EXPORT_DIR, f"flight_data_{timestamp_str}.csv")

    # Define descriptive CSV Headers
    header_cols = [
        'Unix_Timestamp', 'ISO_Time', 
        'Temp1_C', 'Temp2_C', 'Temp3_C', 'Temp4_C', 'Temp5_C',
        'Accel_X', 'Accel_Y', 'Accel_Z',
        'Gyro_X', 'Gyro_Y', 'Gyro_Z',
        'Mag_X', 'Mag_Y', 'Mag_Z',
        'BME_Pressure_hPa', 'BME_Humidity_pct', 'BME_Temp_C',
        'Current_A', 'Power_W', 'Bus_Voltage_V',
        'Is_UTC'
    ]

    count = 0
    with open(output_filename, mode='w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(header_cols)

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

                        if min_ts is not None and ts < min_ts:
                            continue
                        if max_ts is not None and ts > max_ts:
                            continue

                        # --- Data Processing (Matching your original script logic) ---
                        iso_time = datetime.fromtimestamp(ts).isoformat()
                        
                        # INA Calculations
                        current_a = d[18] / 1000.0
                        power_w = d[19] / 1000.0
                        # Bus Voltage: (12000mV rail - shunt voltage)/1000
                        bus_v = (12000 - d[20]) / 1000.0

                        # Build Row
                        # Timestamps + Temps(1-5) + Accel(6-8) + Gyro(9-11) + Mag(12-14) + BME(15-17)
                        row = [ts, iso_time] + list(d[1:18]) 
                        # Append the calculated INA values and the final UTC flag
                        row.extend([current_a, power_w, bus_v, d[21]])
                        
                        writer.writerow(row)
                        count += 1

                    except struct.error:
                        continue
    
    print(f"Export Complete: {count} rows saved to '{output_filename}'")

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