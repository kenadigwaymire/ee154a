import sys
import struct
import os
import time
import random
import smbus2
import bme280
import signal
import datetime
import math

def service_shutdown(signum, frame):
    print(f"Caught signal {signum}. Shutting down mission...")
    raise KeyboardInterrupt  # This forces the 'finally' block to trigger


class FlightStateMachine:
    """
    PURPOSE: Coordinates timing, sensor polling, and CCSDS logging.
    REASONING: Controls the "Mission Loop." 
    """
    def __init__(self, sample_rate=10):
        self.curr_time = time.time()
        self.sample_rate = sample_rate  # Hz
        self.start_time = self.curr_time   # For uptime calculations
        self.camera_rate = 1/60       
        self.last_photo_time = self.curr_time - (1.0 / self.camera_rate) 
        self.loop_start = self.curr_time - (1.0 / self.sample_rate)   
        self.video_duration = 10 # sec 
        self.video_active = False
        self.last_video_time = self.curr_time
        self.camera_mode  = "video"
        self.led_flash_dur = 1.0 # sec
        self.last_led_flash = self.curr_time
        data_folder = "data"

        self.bme280_status = 0
        self.ina219_status = 0
        self.imu_status = 0
        self.temp_status = 0
        self.mpl_status = 0
        self.gps_status = 0
        self.rtc_status = 0
        self.led_status = 0
        self.camera_status = 0
        self.reinit_dur = 30.0 # seconds
        self.last_reinit = self.curr_time
        
        # hardware imports
        try:
            from helpers.imu_sensor import IMUSensor
            from helpers.temp_sensors import TempSensor
            from helpers.ccsds import CCSDSWriter
            from helpers.bme_280 import BME280Sensor
            from helpers.ina219 import INA219Sensor
            from helpers.camera import HQCameraRecorder
            from helpers.mpl3115a2 import MPL3115A2
            from helpers.led import LEDIndicator
            from helpers.rv8803 import RV8803
            from helpers.gp3906 import GP3906

        except ImportError as e:
            print(f"Error importing hardware libraries: {e}")
            print("Make sure you're running this on a Raspberry Pi with the required libraries installed.")
            sys.exit(1)

        try:
            self.logger = CCSDSWriter(apid=0x123, folder=data_folder)
        except Exception as e:
            print(e)
        
        self.initialize_sensors()

    def camera_init(self):
        from helpers.camera import HQCameraRecorder
        try:
            self.camera = HQCameraRecorder()
            self.camera.setup_camera(mode=self.camera_mode)
            self.camera_connected = True
            print("Camera initialized successfully.")
        except Exception as e:
            self.camera_connected = False
            self.camera = None # Set to None so we don't try to call methods on it
            print(f"\n[WARNING] Camera not found or unplugged: {e}")
            print("Mission will continue without imaging.")
    
    def imu_init(self):
        try:
            from helpers.imu_sensor import IMUSensor
            self.imu = IMUSensor()
        except Exception as e:
            self.imu = None
            print(e)

    def temp_init(self):
        try:
            from helpers.temp_sensors import TempSensor
            self.temp = TempSensor()
        except Exception as e:
            self.temp = None
            print(e)

    def bme280_init(self):
        try:
            from helpers.bme_280 import BME280Sensor
            self.bme280 = BME280Sensor()
        except Exception as e:
            self.bme280 = None
            print(e)

    def ina_init(self):
        try:
            from helpers.ina219 import INA219Sensor
            self.ina219 = INA219Sensor()
        except Exception as e:
            self.ina219 = None
            print(e)

    def mpl_init(self):
        try:
            from helpers.mpl3115a2 import MPL3115A2
            self.mpl = MPL3115A2()
        except Exception as e:
            self.mpl = None
            print(e)
            
    def led_init(self):
        try:
            from helpers.led import LEDIndicator
            self.led = LEDIndicator()
        except Exception as e:
            self.led = None
            print(e)
    
    def gps_init(self):
        try:
            from helpers.gp3906 import GP3906
            self.gps = GP3906()
        except Exception as e:
            self.gps = None
            print(e)

    def rtc_init(self):
        try:
            from helpers.rv8803 import RV8803
            self.rtc = RV8803()
        except Exception as e:
            self.rtc = None
            print(e)
    
    def initialize_sensors(self):
        if not self.camera_status:
            self.camera_init()
            if self.camera: self.camera_status = 1

        if not self.imu_status:
            self.imu_init()
            if self.imu: self.imu_status = 1

        if not self.temp_status:
            self.temp_init()
            if self.temp: self.temp_status = 1

        if not self.bme280_status:
            self.bme280_init()
            if self.bme280: self.bme280_status = 1
        if not self.ina219_status:
            self.ina_init()
            if self.ina219: self.ina219_status = 1
        if not self.mpl_status:
            self.mpl_init()
            if self.mpl: self.mpl_status = 1
        if not self.led_status:
            self.led_init()
            if self.led: self.led_status = 1
        if not self.gps_status:
            self.gps_init()
            if self.gps: self.gps_status = 1
        if not self.rtc_status:
            self.rtc_init()
            if self.rtc: self.rtc_status = 1

    def handle_time_sync(self):
        self.curr_time = time.time()
        try:
            if self.rtc:
                if self.rtc.connected:
                    if self.rtc.read_data() != self.curr_time:
                        self.rtc.sync_system_clock()
                        self.curr_time = time.time()
        except Exception as e:
            print(e)

    def handle_data_collection(self):
        nan = float('nan')
        triple_nan = (nan, nan, nan)
        quad_nan = (nan, nan, nan, nan)

        self.loop_start = self.curr_time

        def is_failed(data):
            # Accept list/tuple (and any nested tuples)
            if isinstance(data, (list, tuple)):
                for x in data:
                    if isinstance(x, (list, tuple)):
                        if is_failed(x):
                            return True
                    else:
                        if isinstance(x, float) and math.isnan(x):
                            return True
                return False

            # Single scalar
            return isinstance(data, float) and math.isnan(data)


        # --- RTC STATUS ---
        if self.rtc:
            try:
                t = self.rtc.read_data()
                # print(f"RTC read time: {t}")
                if is_failed(t):
                    rtc_status = 0
                else:
                    rtc_status = 1 
            except Exception as e:
                t = nan
                imu_status = 0
                print(f'RTC read error: {e}')

        else:
            t = nan
            rtc_status = 0

        # --- IMU ---
        if self.imu:
            try:
                accel, gyro, mag = self.imu.get_data()
                # print(f"IMU read accel: {accel}, gyro: {gyro}, mag: {mag}")
                # If any part of the IMU read is NaN, mark as FAIL
                if is_failed(accel) or is_failed(gyro) or is_failed(mag):
                    imu_status = 0
                else:
                    imu_status = 1
            except Exception as e:
                accel, gyro, mag = triple_nan, triple_nan, triple_nan
                imu_status = 0
                print(f'IMU read error: {e}')
                
        else:
            accel, gyro, mag = triple_nan, triple_nan, triple_nan
            imu_status = 0

        # --- TEMPERATURE SENSORS ---
        if self.temp:
            try:
                t_data = self.temp.get_all_temps()
                # print(f"Temp sensor read: {t_data}")
                temp_status = 0 if is_failed(t_data) else 1
            except Exception as e:
                t_data = quad_nan
                temp_status = 0
                print(f'Temp sensor read error: {e}')
        else:
            t_data = quad_nan
            temp_status = 0

        # --- BME280 ---
        if self.bme280:
            try:
                bme_data = self.bme280.get_data()
                # print(f"BME280 read: {bme_data}")
                bme280_status = 0 if is_failed(bme_data) else 1
            except Exception as e:
                bme_data = triple_nan
                bme280_status = 0
                print(f'BME 280 read error: {e}')
        else:
            bme_data = triple_nan
            bme280_status = 0

        # --- INA219 ---
        if self.ina219:
            try:
                ina_data = self.ina219.read_data()
                # print(f"INA219 read: {ina_data}")
                ina219_status = 0 if is_failed(ina_data) else 1
            except Exception as e:
                ina_data = triple_nan
                ina219_status = 0
                print(f'INA 219 read error: {e}')
        else:
            ina_data = triple_nan
            ina219_status = 0

        # --- MPL3115A2 ---
        if self.mpl:
            try:
                mpl_data = self.mpl.read_data()
                # print(f"MPL3115A2 read: {mpl_data}")
                mpl_status = 0 if is_failed(mpl_data) else 1
            except Exception as e:
                mpl_data = nan
                mpl_status = 0
                print(f'MPL read error: {e}')
        else:
            mpl_data = nan
            mpl_status = 0

        # --- GPS ---
        # if self.gps:
        #     try:
        #         gps_data = self.gps.read_data()
        #         print(f"GPS read: {gps_data}")
        #         gps_status = 0 if is_failed(gps_data) else 1
        #     except Exception as e:
        #         gps_data = triple_nan
        #         gps_status = 0
        #         print(f'GPS read error: {e}')
        # else:
        #     gps_data = triple_nan
        #     gps_status = 0

        gps_data = triple_nan
        gps_status = 0

        # Pack for CCSDS (Converts to binary fomat for efficient logging)
        # I = unsigned int (4 bytes), f = float (4 bytes), B = unsigned char (1 byte)
        # print(f"Packing data for CCSDS logging: Time={t}, Temps={t_data}, Accel={accel}, Gyro={gyro}, Mag={mag}, BME={bme_data}, INA={ina_data}, MPL={mpl_data}, GPS={gps_data}, Statuses: RTC={rtc_status}, IMU={imu_status}, Temp={temp_status}, BME280={bme280_status}, INA219={ina219_status}, MPL={mpl_status}, GPS={gps_status}")
        payload = struct.pack(
            ">Iffff fff fff fff fff fff f fff BBBBBBB", 
            int(self.curr_time), 
            *t_data, 
            *accel, 
            *gyro, 
            *mag, 
            *bme_data, 
            *ina_data, 
            mpl_data,
            *gps_data,
            bme280_status, 
            ina219_status, 
            imu_status, 
            temp_status,
            mpl_status,
            gps_status,
            rtc_status
            )
        
        # Log the data in data folder with CCSDS format (Binary)
        # print(f"Logging data to CCSDS: {len(payload)} bytes")
        self.logger.write(payload)

        # print(f"Data collection complete. RTC Status: {rtc_status} | IMU Status: {imu_status} | Temp Status: {temp_status} | BME280 Status: {bme280_status} | INA219 Status: {ina219_status} | MPL Status: {mpl_status} | GPS Status: {gps_status}")
        self.bme280_status = bme280_status
        self.ina219_status = ina219_status
        self.imu_status = imu_status
        self.temp_status = temp_status
        self.mpl_status = mpl_status
        self.gps_status = gps_status
        self.rtc_status = rtc_status

    def handle_reinitialization(self):
        if self.curr_time - self.last_reinit >= self.reinit_dur:
            print("\nAttempting sensor reinitialization...")
            self.initialize_sensors()
            self.last_reinit = self.curr_time
        
    def handle_photos(self):
        if self.curr_time - self.last_photo_time >= (1.0 / self.camera_rate): # Capture at defined camera rate
            try:
                # Take pictures at every interval
                self.camera.take_picture(f"frame_{int(time.time())}.jpg")
            except Exception as e:
                print(f"Error capturing camera frame: {e}")
            self.last_photo_time = time.time()

    def handle_video_recording(self):
        if not self.video_active:
            try:
                self.camera.start_video(f"video_{int(time.time())}.h264")
                self.video_active = True
                self.last_video_time = time.time()
            except Exception as e:
                print(f"Failed to start video: {e}")
        else:
            if self.curr_time - self.last_video_time >= self.video_duration:
                try:
                    self.camera.stop_video()
                    self.video_active = False
                except Exception as e:
                    print(f"Failed to stop video: {e}")

    def run(self):
        """The main mission loop."""
        print(f"Mission Started. Rate: {self.sample_rate}Hz")
        
        try:
            if self.led: self.led.on()
            while True:
                # self.curr_time = time.time()
                self.handle_time_sync()

                # Define loop time to ensure measurement at specified Hz
                elapsed = self.curr_time - self.loop_start
                wait_time = (1.0 / self.sample_rate) - elapsed
                if wait_time > 0: 
                    time.sleep(0.05)
                    # print(f"Waiting {wait_time:.2f}s to maintain sample rate...")
                    continue

                # # Gather data at specified Hz
                # else:
                #     self.handle_data_collection()
                # print(f"Collecting data at {self.curr_time:.2f} (Elapsed: {elapsed:.2f}s)")
                self.handle_data_collection()

                self.handle_reinitialization()

                # Camera Logic (pass if not connecyed)
                if self.camera:
                    if self.camera_connected: 
                        # self.handle_photos()
                        self.handle_video_recording()  

                time.sleep(0.01)  # Short sleep to prevent CPU hogging; adjust as needed
                # break  # Uncomment this to only test one loop iteration; it's here just for testing purposes.


        # Handle graceful exit
        except KeyboardInterrupt:
            print("Ending script")
        finally:
            print("\nCleaning up GPIO...")
            try:
                if self.camera:
                    self.camera.cleanup()
            except:
                pass
            try:
                if self.led:
                    self.led.off() 
                    self.led.cleanup()
            except:
                pass
            import RPi.GPIO as GPIO
            GPIO.cleanup()           

if __name__ == "__main__":  
    # tells watchdog script to run cleanup
    signal.signal(signal.SIGTERM, service_shutdown)
    signal.signal(signal.SIGINT, service_shutdown)

    # Pass that result into your class
    mission = FlightStateMachine(sample_rate=10)
    mission.run()