import os
import time
import sys
import struct
import glob
from helpers.ccsds import CCSDSReader

class TerminalDashboard:
    """Renders the UI to the terminal."""
    def __init__(self, mission_name="AstroPi Mission 2026"):
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
            print("PUT ERRORS HERE IF NEEDED")
            print("=" * 50)
        except Exception as e:
            print(f"Display Error: {e}")

class GroundStation:
    """Handles the data stream and unpacking."""
    PAYLOAD_FORMAT = ">Ifffff fff fff fff fff B"

    def __init__(self, simulate=False):
        self.data_folder = "simulated-data" if simulate else "data"
        self.reader = CCSDSReader(folder=self.data_folder)
        self.dash = TerminalDashboard(mission_name="Fuck u")

    def run(self):
        filepath = os.path.join(self.data_folder, "telemetry.ccsds")
        print(f"Ground Station Active. Monitoring Live: {filepath}")
        
        # Ensure the file exists before trying to open it
        while not os.path.exists(filepath):
            self.dash.display_message("WAITING FOR FILE - telemetry.ccsds not found...")
            time.sleep(1)

        with open(filepath, "rb") as f:
            # JUMP TO THE END: Skip all historical data to get only the current line
            f.seek(0, os.SEEK_END)
            
            try:
                while True:
                    curr_pos = f.tell()
                    header_data = f.read(6)
                    
                    if len(header_data) < 6:
                        # No new packet yet. Reset the pointer to where the header should start
                        f.seek(curr_pos)
                        time.sleep(0.05) # Check 20 times per second
                        continue
                    
                    # Unpack the 6-byte CCSDS header
                    header = struct.unpack(">HHH", header_data)
                    length = header[2] + 1
                    
                    # Read the payload based on the length in the header
                    payload = f.read(length)
                    
                    if len(payload) < length:
                        # Packet is incomplete (being written). Reset to start of header.
                        f.seek(curr_pos)
                        time.sleep(0.05)
                        continue

                    # Success! Unpack and display the live data
                    try:
                        unpacked_data = struct.unpack(self.PAYLOAD_FORMAT, payload)
                        self.dash.display(unpacked_data)
                    except struct.error:
                        # Handle corrupted packets or format mismatches
                        continue

            except KeyboardInterrupt:
                print("\n[GS] Ground Station Offline.")

if __name__ == "__main__":
    is_sim = "--simulate" in sys.argv
    gs = GroundStation(simulate=is_sim)
    gs.run()