# EE 154A - Weather Balloon Payload

Raspberry Pi-based sensor payload for a high-altitude weather balloon. Built across four labs, progressing from standalone sensor experiments to a fully integrated flight computer.

---

## Repository Layout

```
ee154a/
├── lab2/               # Standalone: IMU + Thermistors
├── lab3/               # Standalone: Full sensor suite with CCSDS logging
├── lab4/               # FLIGHT CODE (runs on the balloon)
│   ├── helpers/        #   Sensor drivers and utilities
│   ├── data/           #   Binary telemetry output (.ccsds files)
│   ├── media/          #   Photos and video captured in flight
│   └── readme.txt      #   Quick-reference for SSH, commands, and running scripts
└── misc/               # Miscellaneous data files and early experiments
```

---

## Lab Descriptions

### Lab 2 - IMU and Temperature Sensors (Standalone)

First hardware bring-up. Reads the **MPU9250** 9-axis IMU (accelerometer, gyroscope, magnetometer) and **4 thermistors** through two **ADS1115** ADCs. Converts raw ADC voltages to temperature using the Steinhart-Hart equation. Data is logged to CSV at ~346 Hz and a GPIO pin drives an alert LED when any temperature exceeds 30 C.

Key files:
- `main.py` - Sensor initialization, data loop, CSV export
- `bme280.py` - Early standalone BME280 test script
- `plot_data.py` / `csv_exporter.py` - Post-processing utilities

### Lab 3 - Full Sensor Integration with CCSDS (Standalone)

Adds the **BME280** (temperature, pressure, humidity), **INA219** (bus voltage, current, power), and a **Raspberry Pi HQ Camera**. Replaces CSV logging with **CCSDS Space Packet Protocol** binary logging for compact, space-standard data storage. Introduces a `helpers/` module structure so each sensor has its own driver class.

Also includes:
- `launch.py` - Opens the flight state machine, ground terminal, and live plotter in separate terminal windows
- `log_to_terminal.py` - Live terminal dashboard that reads the latest CCSDS packet and displays sensor values
- `active_plot.py` - Real-time matplotlib graphs
- `ccsds_to_csv.py` - Converts binary telemetry back to CSV with optional date filtering
- `plot.py` - Generates and saves graphs from recorded data to `graphs/`

### Lab 4 - Flight Code (Runs on the Balloon)

The production code that actually flies. Builds on Lab 3 with additional hardware and improved reliability:

**New sensors added:**
- **MPL3115A2** - Barometric altimeter (altitude in feet)
- **GP3906** - GPS module (latitude, longitude, altitude via NMEA sentences)
- **RV8803** - Real-time clock for accurate timestamping and system clock sync

**New features over Lab 3:**
- Every sensor initializes independently; if one fails the mission continues with NaN placeholders
- Every so often the script reinitializes any failed sensors to try and get them back up and running
- Status flags (OK/FAIL) are packed into every CCSDS packet for each sensor to check if we can read the data or not
- LED indicator on GPIO 26 signals that the flight computer is alive (necessary for background functionality)
- Video recording mode (Currently 5-second clips, H.264, 480p @ 30fps) in addition to still capture
  - We can only choose still or video mode since initicalizing the camera takes quite a while relative to the data capture. Thus, we are only using video for now 
- RTC syncs the Pi system clock on each loop iteration to maintain accurate time without network
- Watchdog-style systemd service auto-restarts the script on crash after 5 seconds or after the Pi's bootup sequence

**Data format:** Each CCSDS packet contains a 6-byte header followed by a binary payload:
```
Timestamp (uint32) | 4 Temps (float x4) | Accel XYZ (float x3) | Gyro XYZ (float x3) |
Mag XYZ (float x3) | BME Temp/Press/Hum (float x3) | INA Volt/Curr/Pwr (float x3) |
MPL Altitude (float) | GPS Lat/Lon/Alt (float x3) | Status flags (uint8 x7)
```

Key files:
- `flight_state_machine.py` - Main mission loop (this is what the watchdog runs)
- `terminal_debugger.py` - Live telemetry dashboard over SSH
- `plot.py` - Post-flight graphing with optional `--minDate` / `--maxDate` filters
- `ccsds_to_csv.py` - Export binary data to CSV for analysis
- `set_rtc_time.py` - Manually sync the RV8803 RTC
- `readme.txt` - SSH credentials, watchdog commands, and how to run each script

---

## Hardware

| Sensor / Module | What It Measures | Interface | Driver File |
|---|---|---|---|
| MPU9250 | Acceleration, angular rate, magnetic field (9-axis) | I2C | `helpers/imu_sensor.py` |
| ADS1115 (x1) | 4 thermistor channels via ADC | I2C | `helpers/temp_sensors.py` |
| BME280 | Ambient temperature, barometric pressure, humidity | I2C | `helpers/bme_280.py` |
| INA219 | Bus voltage, current draw, power consumption | I2C | `helpers/ina219.py` |
| MPL3115A2 | Barometric altitude | I2C | `helpers/mpl3115a2.py` |
| GP3906 | GPS position (lat, lon, alt) | UART | `helpers/gp3906.py` |
| RV8803 | Real-time clock (epoch time, system clock sync) | I2C | `helpers/rv8803.py` |
| RPi HQ Camera | Still photos and H.264 video | CSI | `helpers/camera.py` |
| LED (GPIO 26) | Status indicator | GPIO | `helpers/led.py` |

---

## CCSDS Logging

All telemetry is stored in binary using the **CCSDS Space Packet Protocol** (`helpers/ccsds.py`). This was chosen because:

1. **Compact** - Binary packing is 3-10x smaller than CSV or JSON, important for limited storage
2. **Standardized** - CCSDS headers are parseable by standard NASA/ESA ground tools
3. **Resilient** - Files auto-rotate at 10 MB and every write is flushed + fsynced to survive power loss

The `CCSDSReader` class handles decoding. Both `plot.py` and `ccsds_to_csv.py` use it to parse flight data back into usable formats.

---

## Running the Flight Code (Lab 4)

See `lab4/readme.txt` for the full quick-reference. Summary:

**SSH into the Pi:**
```
ssh ee154@10.8.18.185
# password: raspberry23
```

**Watchdog commands (systemd service):**
```
mission-start       # Start the flight script
mission-stop        # Stop temporarily
mission-log         # View live script output
mission-enable      # Enable auto-start on boot
mission-disable     # Disable auto-start
feed-start          # Open terminal_debugger.py
```

**Manual operation (requires venv):**
```
# How to activate VENV
cd ee154
source .venv/bin/activate

# How to run code (make sure you are in lab4 folder so data paths properly)
cd lab4
python flight_state_machine.py                                          # Run the mission loop directly
python terminal_debugger.py                                             # Live telemetry display
python plot.py                                                          # Plot all data
python plot.py --minDate="02/14/2026|12:00:00" --maxDate="02/14/2026|23:59:59"  # Filter by time
python ccsds_to_csv.py                                                  # Export all to CSV
python ccsds_to_csv.py --minDate="02/14/2026|08:00:00"                  # Export filtered
```

---

## Misc Folder

Contains early test data and reference files from Lab 2 experiments:
- `requirements.txt` - Python dependencies for the Pi
- `temp-data-control-REAL-USE-THIS-ONE.csv` - Baseline thermistor data used for calibration
- `lab2-data`, `temp-control.csv`, `temp-varied-data`, `test1` - Raw experimental data
