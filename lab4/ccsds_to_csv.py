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

    files = sorted(glob.glob(os.path.join(folder_path, "*.ccsds")))
    if not files:
        print(f"No data found in {folder_path}")
        return

    timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_filename = os.path.join(EXPORT_DIR, f"flight_data_{timestamp_str}.csv")

    # Expanded headers to include GPS and all Status Flags
    header_cols = [
        'Unix_Timestamp', 'ISO_Time', 
        'Temp1', 'Temp2', 'Temp3', 'Temp4',
        'Accel_X', 'Accel_Y', 'Accel_Z',
        'Gyro_X', 'Gyro_Y', 'Gyro_Z',
        'Mag_X', 'Mag_Y', 'Mag_Z',
        'BME_Temp', 'BME_Pres', 'BME_Hum',
        'MPL_Alt_m', 'Lat', 'Lon', 'GPS_Alt',
        'Volt_V', 'Curr_A', 'Power_W',
        'Stat_BME', 'Stat_INA', 'Stat_IMU', 'Stat_Temp', 'Stat_MPL', 'Stat_GPS', 'Stat_RTC'
    ]

    count = 0
    expected_size = struct.calcsize(PAYLOAD_FORMAT)

    with open(output_filename, mode='w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(header_cols)

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

                        if min_ts and ts < min_ts: continue
                        if max_ts and ts > max_ts: continue

                        iso_time = datetime.fromtimestamp(ts).isoformat()

                        # Apply the same math fixes from terminal_debugger.py
                        curr_a = d[20] / -1000.0  # INA Current fix
                        pwr_w = d[21] / 1000.0    # INA Power fix
                        mpl_m = d[18] / 3.28084   # MPL Altitude fix (ft to m)

                        # Row Construction
                        # ts, iso, t1-t4(1:5), accel/gyro/mag/bme(5:18)
                        row = [ts, iso_time] + list(d[1:18]) 
                        # mpl, lat, lon, gps_alt, volt, curr, pwr, status_flags
                        row.extend([mpl_m, d[19], d[20], d[21], d[19], curr_a, pwr_w])
                        row.extend(list(d[22:])) # Add the 7 status bytes
                        
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
