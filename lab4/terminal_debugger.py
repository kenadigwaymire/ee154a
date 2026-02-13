import os
import time
import sys
import struct
import glob
from helpers.ccsds import CCSDSReader

class TerminalDashboard:
    """Renders the UI to the terminal."""
    def __init__(self, mission_name="System Debug Terminal"):
        self.mission_name = mission_name
        self.start_time = time.time()

    def clear_screen(self):
        os.system('cls' if os.name == 'nt' else 'clear')

    def display_message(self, message):
        """Displays a simple status message without crashing."""
        self.clear_screen()
        print(f"[{self.mission_name}] STATUS: {message}")

    def display(self, data_packet):
        try:
            t = data_packet
            self.clear_screen()
            print("=" * 50)
            print(f" {self.mission_name} - LIVE TELEMETRY")
            print("=" * 50)
            uptime = time.time() - self.start_time
            print(f"TIMESTAMP: {int(t[0])} | UPTIME: {int(uptime)}s | TIMEZONE: {'UTC' if t[18] else 'LOC'}")
            print("-" * 50)
            print(f"TEMPERATURES (°C):")
            print(f"  T1: {t[1]:.2f} | T2: {t[2]:.2f} | T3: {t[3]:.2f} | T4: {t[4]:.2f} | T5: {t[5]:.2f}")
            print("-" * 50)
            print(f"ACCEL (m/s²):  X: {t[6]:>7.2f}  Y: {t[7]:>7.2f}  Z: {t[8]:>7.2f}")
            print(f"GYRO  (rad/s): X: {t[9]:>7.2f}  Y: {t[10]:>7.2f}  Z: {t[11]:>7.2f}")
            print(f"MAG   (μT):    X: {t[12]:>7.2f}  Y: {t[13]:>7.2f}  Z: {t[14]:>7.2f}")
            print("-" * 50)
            print(f"BME280: Pressure: {t[16]:.2f} hPa | Humidity: {t[17]:.2f}% | Temp: {t[15]:.2f}°C")
            print("-" * 50)
            print(f"INA219: Voltage: {t[21]:.2f} mV | Current: {t[19]:.2f} mA | Power: {t[20]:.2f} W")
            print("-" * 50)
            print("SENSOR STATUS: " +
                  f"BME280: {'OK' if t[22] else 'FAIL'} | " +
                  f"INA219: {'OK' if t[23] else 'FAIL'} | " +
                  f"IMU: {'OK' if t[24] else 'FAIL'} | " +
                  f"Temp: {'OK' if t[25] else 'FAIL'}")
            print("=" * 50)
        except Exception as e:
            print(f"Display Error: {e}")

class GroundStation:
    """Handles the data stream and unpacking."""
    PAYLOAD_FORMAT = ">Ifffff fff fff fff fff fff B"

    def __init__(self, simulate=False):
        self.data_folder = "simulated-data" if simulate else "data"
        self.reader = CCSDSReader(folder=self.data_folder)
        self.dash = TerminalDashboard(mission_name="Fuck u")

    def run(self):
        print(f"Ground Station Active. Monitoring: {self.data_folder}")
        
        try:
            while True:
                # Check if folder exists or has files
                files = glob.glob(os.path.join(self.data_folder, "*.ccsds"))
                
                if not files:
                    self.dash.display_message("NO DATA DETECTED - Waiting for Mission Start...")
                    time.sleep(2)
                    continue

                # Stream the files
                found_valid_packet = False
                for packet_dict in self.reader.stream_all_files():
                    found_valid_packet = True
                    raw_payload = packet_dict["payload"]
                    
                    try:
                        unpacked_data = struct.unpack(self.PAYLOAD_FORMAT, raw_payload)
                        self.dash.display(unpacked_data)
                        time.sleep(0.1) # Refresh rate
                    except struct.error:
                        # Don't crash on one bad packet, just skip it
                        continue
                
                if not found_valid_packet:
                    self.dash.display_message("INVALID DATA - Files found but packets are unreadable.")
                    time.sleep(2)

        except KeyboardInterrupt:
            print("\n[GS] Ground Station Offline.")

if __name__ == "__main__":
    is_sim = "--simulate" in sys.argv
    gs = GroundStation(simulate=is_sim)
    gs.run()