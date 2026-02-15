import sys
import struct
import os
import time
import random
import smbus2
import bme280
import signal

def service_shutdown(signum, frame):
    print(f"Caught signal {signum}. Shutting down mission...")
    raise KeyboardInterrupt  # This forces the 'finally' block to trigger


class FlightStateMachine:
    """
    PURPOSE: Coordinates timing, sensor polling, and CCSDS logging.
    REASONING: Controls the "Mission Loop." 
    """
    def __init__(self, sample_rate=10):
        curr_time = time.time()
        self.sample_rate = sample_rate  # Hz
        self.start_time = curr_time   # For uptime calculations
        self.camera_rate = 1/60       
        self.last_photo_time = curr_time - (1.0 / self.camera_rate) 
        self.loop_start = curr_time - (1.0 / self.sample_rate)   
        self.video_duration = 10 # sec 
        self.video_active = False
        self.last_video_time = curr_time
        self.camera_mode  = "video"
        self.led_flash_dur = 1.0 # sec
        self.last_led_flash = curr_time
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

        except ImportError as e:
            print(f"Error importing hardware libraries: {e}")
            print("Make sure you're running this on a Raspberry Pi with the required libraries installed.")
            sys.exit(1)

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

        try:
            # Initialize Hardware
            self.imu = IMUSensor()
            self.temp = TempSensor()
            self.bme280 = BME280Sensor()
            self.ina219 = INA219Sensor()
            self.logger = CCSDSWriter(apid=0x123, folder=data_folder)
            self.mpl = MPL3115A2()
            self.led = LEDIndicator()

        # Handle initialization errors
        except Exception as e:
            print(f"\nError Initializing Hardware: {e}")
            sys.exit(1) # Stop the script so it doesn't just 'vanish'

    def run(self):
        """The main mission loop."""
        print(f"Mission Started. Rate: {self.sample_rate}Hz")
        try:
            self.led.on()
            while True:
                curr_time = time.time()
                elapsed = curr_time - self.loop_start
                wait_time = (1.0 / self.sample_rate) - elapsed
                if wait_time > 0: 
                    continue
                else:
                    self.loop_start = curr_time
                    # # Flash LED Example
                    # if curr_time - self.last_led_flash >= self.led_flash_dur:
                    #     self.led.toggle()
                    #     self.last_led_flash = curr_time

                    # Collect sensor data
                    accel, gyro, mag = self.imu.get_data()
                    t_data = self.temp.get_all_temps()
                    bme_data = self.bme280.get_data()
                    ina_data = self.ina219.read_data()
                    mpl_data = self.mpl.read_data()

                    # Get status of each  
                    bme280_status = 1 if self.bme280.connected else 0
                    ina219_status = 1 if self.ina219.connected else 0
                    imu_status = 1 if self.imu.connected else 0
                    temp_status = 1 if self.temp.connected else 0
                    mpl_status = 1 if self.temp.connected else 0

                    # Pack for CCSDS (Converts to binary fomat for efficient logging)
                    # I = unsigned int (4 bytes), f = float (4 bytes), B = unsigned char (1 byte)
                    payload = struct.pack(
                        ">Iffff fff fff fff fff fff f BBBBB", 
                        int(curr_time), 
                        *t_data, 
                        *accel, 
                        *gyro, 
                        *mag, 
                        *bme_data, 
                        *ina_data, 
                        mpl_data,
                        bme280_status, 
                        ina219_status, 
                        imu_status, 
                        temp_status,
                        mpl_status
                        )
                    
                    # Log the data in data folder with CCSDS format (Binary)
                    self.logger.write(payload)

                # Camera Logic (pass if not connecyed)
                if not self.camera_connected: continue

                # # Photo Logic
                # if curr_time - self.last_photo_time >= (1.0 / self.camera_rate): # Capture at defined camera rate
                #     try:
                #         # Take pictures at every interval
                #         self.camera.take_picture(f"frame_{int(time.time())}.jpg")
                #     except Exception as e:
                #         print(f"Error capturing camera frame: {e}")
                #     self.last_photo_time = time.time()

                # # Video Logic
                # if not self.video_active:
                #     try:
                #         self.camera.start_video(f"video_{int(time.time())}.h264")
                #         self.video_active = True
                #         self.last_video_time = time.time()
                #     except Exception as e:
                #         print(f"Failed to start video: {e}")
                # else:
                #     if curr_time - self.last_video_time >= self.video_duration:
                #         try:
                #             self.camera.stop_video()
                #             self.video_active = False
                #         except Exception as e:
                #             print(f"Failed to stop video: {e}")

                # break  # Uncomment this to only test one loop iteration; it's here just for testing purposes.


        # Handle graceful exit
        except KeyboardInterrupt:
            print("Ending script")
        finally:
            print("\nCleaning up GPIO...")
            try:
                self.camera.cleanup()
            except:
                pass
            try:
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