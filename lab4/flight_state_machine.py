import sys
import struct
import os
import time
import random
import smbus2
import bme280

class FlightStateMachine:
    """
    PURPOSE: Coordinates timing, sensor polling, and CCSDS logging.
    REASONING: Controls the "Mission Loop." Can run on a laptop (Simulation) 
               or on the ISS hardware (Flight).
    """
    def __init__(self, sample_rate=10):
        self.sample_rate = sample_rate  # Hz
        self.start_time = time.time()   # For uptime calculations
        self.camera_rate = 1/60       
        self.last_camera_time = time.time() - (1.0 / self.camera_rate) 
        self.loop_start = time.time() - (1.0 / self.sample_rate)    
        data_folder = "data"
        
        # hardware imports
        try:
            from helpers.imu_sensor import IMUSensor
            from helpers.temp_sensors import TempSensor
            from helpers.ccsds import CCSDSWriter
            from helpers.bme_280 import BME280Sensor
            from helpers.ina219 import INA219Sensor
            from helpers.camera import HQCameraRecorder
        except ImportError as e:
            print(f"Error importing hardware libraries: {e}")
            print("Make sure you're running this on a Raspberry Pi with the required libraries installed.")
            sys.exit(1)
        
        try:
            # Initialize Hardware
            self.imu = IMUSensor()
            self.temp = TempSensor()
            self.bme280 = BME280Sensor()
            self.ina219 = INA219Sensor()
            self.camera = HQCameraRecorder()
            self.camera.setup_camera(mode="still")  # Initialize camera in still mode TODO add video mode later
            
            self.logger = CCSDSWriter(apid=0x123, folder=data_folder)
            self.is_utc_valid = True  # TODO: In a real mission, you'd check if the RTC is set to UTC time.

        # Handle initialization errors
        except Exception as e:
            print(f"\nError Initializing Hardware: {e}")
            sys.exit(1) # Stop the script so it doesn't just 'vanish'

    def run(self):
        """The main mission loop."""
        print(f"Mission Started. Rate: {self.sample_rate}Hz")
        try:
            while True:
                # Precise Timing
                elapsed = time.time() - self.loop_start
                wait_time = (1.0 / self.sample_rate) - elapsed
                if wait_time > 0: continue

                self.loop_start = time.time()

                # Collect Data Using Sensor Classes     
                accel, gyro, mag = self.imu.get_data()
                t_data = self.temp.get_all_temps()
                bme_data = self.bme280.get_data()
                ina_data = self.ina219.read_data()
  
                # Timestamp Logic
                current_time = time.time()
                is_utc = 1 if self.is_utc_valid else 0 #TODO, look at this for realtime clock logic, this is just a placeholder

                # Pack for CCSDS (Converts to binary fomat for efficient logging)
                # I = unsigned int (4 bytes), f = float (4 bytes), B = unsigned char (1 byte)
                payload = struct.pack(">Ifffff fff fff fff fff fff B", 
                    int(current_time), *t_data, *accel, *gyro, *mag, *bme_data, *ina_data, is_utc)
                
                # Log the data in data folder with CCSDS format (Binary)
                self.logger.write(payload)

                # Camera Logic: Capture a photo #TODO add video mode later, this is just a placeholder for now
                if time.time() - self.last_camera_time >= (1.0 / self.camera_rate):
                    try:
                        self.camera.take_picture(f"frame_{int(time.time())}.jpg")
                    except Exception as e:
                        print(f"Error capturing camera frame: {e}")
                    self.last_camera_time = time.time()

                # break  # Remove this line to run indefinitely; it's here just for testing purposes.

        # Handle graceful exit
        except KeyboardInterrupt:
            print("\nCleaning up GPIO...")
            self.camera.cleanup() 
            import RPi.GPIO as GPIO
            GPIO.cleanup()
           

if __name__ == "__main__":    
    # Pass that result into your class
    mission = FlightStateMachine(sample_rate=10)
    mission.run()