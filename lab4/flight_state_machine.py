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
        self.camera_init()
        self.imu_init()
        self.temp_init()
        self.bme280_init()
        self.ina_init()
        self.mpl_init()
        self.led_init()
        self.gps_init()
        self.rtc_init()

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
            if isinstance(data, tuple):
                return any(math.isnan(x) for x in data)
            return math.isnan(data)

        # --- RTC STATUS ---
        if self.rtc:
            try:
                t = self.rtc.read_data()
                rtc_status = 1
            except Exception:
                t = nan
                imu_status = 0

        else:
            t = nan
            rtc_status = 0

        # --- IMU ---
        if self.imu:
            try:
                accel, gyro, mag = self.imu.get_data()
                # If any part of the IMU read is NaN, mark as FAIL
                if is_failed(accel) or is_failed(gyro) or is_failed(mag):
                    imu_status = 0
                else:
                    imu_status = 1
            except Exception:
                accel, gyro, mag = triple_nan, triple_nan, triple_nan
                imu_status = 0
        else:
            accel, gyro, mag = triple_nan, triple_nan, triple_nan
            imu_status = 0

        # --- TEMPERATURE SENSORS ---
        if self.temp:
            try:
                t_data = self.temp.get_all_temps()
                temp_status = 0 if is_failed(t_data) else 1
            except Exception:
                t_data = quad_nan
                temp_status = 0
        else:
            t_data = quad_nan
            temp_status = 0

        # --- BME280 ---
        if self.bme280:
            try:
                bme_data = self.bme280.get_data()
                bme280_status = 0 if is_failed(bme_data) else 1
            except Exception:
                bme_data = triple_nan
                bme280_status = 0
        else:
            bme_data = triple_nan
            bme280_status = 0

        # --- INA219 ---
        if self.ina219:
            try:
                ina_data = self.ina219.read_data()
                ina219_status = 0 if is_failed(ina_data) else 1
            except Exception:
                ina_data = triple_nan
                ina219_status = 0
        else:
            ina_data = triple_nan
            ina219_status = 0

        # --- MPL3115A2 ---
        if self.mpl:
            try:
                mpl_data = self.mpl.read_data()
                mpl_status = 0 if is_failed(mpl_data) else 1
            except Exception:
                mpl_data = nan
                mpl_status = 0
        else:
            mpl_data = nan
            mpl_status = 0

        # --- GPS ---
        if self.gps:
            try:
                gps_data = self.gps.read_data()
                gps_status = 0 if is_failed(gps_data) else 1
            except Exception:
                gps_data = triple_nan
                gps_status = 0
        else:
            gps_data = triple_nan
            gps_status = 0

        # Pack for CCSDS (Converts to binary fomat for efficient logging)
        # I = unsigned int (4 bytes), f = float (4 bytes), B = unsigned char (1 byte)
        payload = struct.pack(
            ">Iffff fff fff fff fff fff fff f BBBBBBB", 
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
        self.logger.write(payload)

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
                self.handle_time_sync()

                # Define loop time to ensure measurement at specified Hz
                elapsed = self.curr_time - self.loop_start
                wait_time = (1.0 / self.sample_rate) - elapsed
                if wait_time > 0: 
                    continue

                # Gather data at specified Hz
                else:
                    self.handle_data_collection()

                # Camera Logic (pass if not connecyed)
                if not self.camera:
                    continue
                if not self.camera_connected: 
                    continue
            

                # CHOOSE ONLY ONE OF THESE AND CHANGE MODE IN INIT
                # self.handle_photos()
                # self.handle_video_recording()  

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