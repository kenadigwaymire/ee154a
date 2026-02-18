import os
import time
import sys
import struct
import glob
from helpers.ccsds import CCSDSReader

class TerminalDashboard:
    def __init__(self, mission_name="System Debug Terminal"):
        self.mission_name = mission_name
        self.start_time = time.time()

    def clear_screen(self):
        os.system('cls' if os.name == 'nt' else 'clear')

    def display(self, data_packet):
        try:
            # --- 1. NAMED UNPACKING ---
            # This must match  PAYLOAD_FORMAT exactly
            (
                ts, 
                t1, t2, t3, t4,                  # 4 Temps
                ax, ay, az,                      # Accel
                gx, gy, gz,                      # Gyro
                mx, my, mz,                      # Mag
                bme_temp, bme_pres, bme_hum,     # BME280
                ina_volt, ina_curr, ina_pwr,     # INA219
                mpl,
                lat, long, alt,
                stat_bme, stat_ina, stat_imu, stat_temp, stat_mpl, stat_gps, stat_rtc # BBBBB (Status Flags)
            ) = data_packet

            self.clear_screen()
            uptime = time.time() - self.start_time

            print("=" * 55)
            print(f" {self.mission_name} - LIVE TELEMETRY")
            print("=" * 55)
            print(f"TIME: {int(ts)} | UPTIME: {int(uptime)}s")
            print("-" * 55)
            
            print(f"TEMPERATURES (°C):")
            print(f"  T1:{t1:>5.1f} T2:{t2:>5.1f} T3:{t3:>5.1f} T4:{t4:>5.1f}")
            print(f"  BME Temp: {bme_temp:.2f}°C")
            print("-" * 55)
            
            print(f"IMU DATA:")
            print(f"  ACCEL (m/s²):  X:{ax:>6.2f}  Y:{ay:>6.2f}  Z:{az:>6.2f}")
            print(f"  GYRO  (rad/s): X:{gx:>6.2f}  Y:{gy:>6.2f}  Z:{gz:>6.2f}")
            print(f"  MAG   (μT):    X:{mx:>6.2f}  Y:{my:>6.2f}  Z:{mz:>6.2f}")
            print("-" * 55)
            
            print(f"ENVIRONMENT & POWER:")
            print(f"  BME: {bme_pres:>7.2f} hPa | {bme_hum:>5.2f}% Hum")
            print(f"  INA: {ina_volt:>7.2f} mV  | {ina_curr:>7.2f} mA | {ina_pwr:>5.2f} W")
            print(f"  MPL: {mpl:>7.2f} ft")
            print(f"  GPS: {lat:>7.2f} deg  | {long:>7.2f} deg | {alt:>5.2f} m")
            print("-" * 55)
            
            # Helper to colorize status
            def ok(val): return "\033[92mOK\033[0m" if val else "\033[91mFAIL\033[0m"
            
            print(f"SENSOR STATUS:")
            print(f"  BME280: {ok(stat_bme)} | INA219: {ok(stat_ina)} | IMU: {ok(stat_imu)}")
            print(f"  TEMPS:  {ok(stat_temp)} | MPL: {ok(stat_mpl)} | GPS: {ok(stat_gps)}")
            print(f"  RTC:  {ok(stat_rtc)}")
            print("=" * 55)

        except Exception as e:
            print(f"Display Error: {e}")

class GroundStation:
    """Handles the data stream and unpacking."""
    PAYLOAD_FORMAT = ">Iffff fff fff fff fff fff f fff BBBBBBB" # Must match the struct.pack format in flight code

    def __init__(self, simulate=False):
        self.data_folder = "simulated-data" if simulate else "data"
        self.reader = CCSDSReader(folder=self.data_folder)
        self.dash = TerminalDashboard(mission_name="Payload #3")

    def run(self):
        print(f"Ground Station Active. Monitoring: {self.data_folder}")
        
        try:
            while True:
                # 1. Always look for the LATEST file (sorted by name/time)
                files = sorted(glob.glob(os.path.join(self.data_folder, "*.ccsds")))
                
                if not files:
                    print("NO DATA DETECTED - Waiting...")
                    time.sleep(1)
                    continue

                latest_file = files[-1] # Grab the newest file
                
                # 2. Open the file and jump to the end
                with open(latest_file, "rb") as f:
                    file_size = os.path.getsize(latest_file)
                    
                    if file_size < 6: # File is empty or just started
                        time.sleep(0.5)
                        continue

                    # We want the LAST packet. 
                    # A safe bet is to look at the last 1024 bytes to find a header
                    # Or, more simply, we use your reader's specific file logic
                    packets = list(self.reader.stream_specific_file(latest_file))
                    
                    if packets:
                        latest_packet = packets[-1] # The last entry in the list
                        raw_payload = latest_packet["payload"]
                        
                        try:
                            unpacked_data = struct.unpack(self.PAYLOAD_FORMAT, raw_payload)
                            self.dash.display(unpacked_data)
                        except struct.error as e:
                            # Skip if the very last packet was partially written
                            continue
                
                # High refresh for a "live" feel
                time.sleep(0.2) 

        except Exception as e:
            print(f"Failed: {e}")
        except KeyboardInterrupt:
            print("\n[GS] Ground Station Offline.")

if __name__ == "__main__":
    gs = GroundStation()
    gs.run()