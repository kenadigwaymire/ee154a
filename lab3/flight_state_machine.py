import sys
import struct
import os
import time
import random
from unittest.mock import MagicMock
import smbus2
import bme280

class FlightStateMachine:
    """
    PURPOSE: Coordinates timing, sensor polling, and CCSDS logging.
    REASONING: Controls the "Mission Loop." Can run on a laptop (Simulation) 
               or on the ISS hardware (Flight).
    """
    def __init__(self, sample_rate=10, simulate=False):
        self.simulate = simulate        # Simulation mode for pc testing
        self.sample_rate = sample_rate  # Hz
        self.start_time = time.time()   # For uptime calculations

        # Reminder: you are working in simulation mode
        if self.simulate:
            self._setup_simulation()
            print("--- INITIALIZED IN SIMULATION MODE ---")
        
        # hardware imports
        try:
            from helpers.imu_sensor import IMUSensor
            from helpers.temp_sensors import TempSensor
            from helpers.ccsds import CCSDSWriter
            from helpers.bme_280 import BME280Sensor

            # Initialize Hardware
            self.imu = IMUSensor()
            self.temp = TempSensor()
            self.bme280 = BME280Sensor()
            
            data_folder = "simulated-data" if self.simulate else "data"
            self.logger = CCSDSWriter(apid=0x123, folder=data_folder)
            self.is_utc_valid = not self.simulate 

        # Handle initialization errors
        except Exception as e:
            print(f"\n[CRITICAL ERROR]: {e}")
            sys.exit(1) # Stop the script so it doesn't just 'vanish'

    def _setup_simulation(self):
        """Injects fake modules into the system to prevent crashes on laptops.
        
        MagicMock is used to create dummy classes and constants that mimic
        the real hardware libraries, allowing the rest of the code to run"""

        # Define Registers/Constants
        mock_regs = MagicMock()
        mock_regs.AK8963_ADDRESS = 0x0C
        mock_regs.MPU9050_ADDRESS_68 = 0x68
        mock_regs.AK8963_BIT_16 = 0x01
        mock_regs.AK8963_MODE_C100HZ = 0x06
        mock_regs.GFS_1000 = 0x02
        mock_regs.AFS_8G = 0x02

        # Inject Modules
        mocks = ["RPi", "RPi.GPIO", "ADS1x15", "mpu9250_jmdev", 
                 "mpu9250_jmdev.registers", "mpu9250_jmdev.mpu_9250"]
        
        for module in mocks:
            sys.modules[module] = MagicMock()
        
        # Attach Constants
        sys.modules["mpu9250_jmdev.registers"] = mock_regs
        
        # Define Fake Hardware Classes
        class MockADS:
            def __init__(self, bus, address): self.PGA_4_096V = 4.096
            # def 

        class MockMPU:
            def __init__(self, **kwargs): pass
            # def configure(self): pass
            # def readAccelerometerMaster(self): return (0.0, 0.0, 9.8 + random.uniform(-0.1, 0.1))
            # def readGyroscopeMaster(self): return (random.uniform(-0.1, 0.1), 0.0, 0.0)
            # def readMagnetometerMaster(self): return (30.0 + random.uniform(-1, 1), 0.0, 0.0)

        import ADS1x15
        ADS1x15.ADS1115 = MockADS

        import mpu9250_jmdev.mpu_9250
        mpu9250_jmdev.mpu_9250.MPU9250 = MockMPU
        
        import RPi.GPIO as GPIO
        GPIO.BCM, GPIO.OUT, GPIO.HIGH, GPIO.LOW = 11, 1, 1, 0


    def run(self):
        """The main mission loop."""
        print(f"Mission Started. Rate: {self.sample_rate}Hz")
        try:
            while True:
                loop_start = time.time()

                # 1. Collect Data       
                if self.simulate:
                    t_data = [20.0 + random.uniform(-0.5, 0.5) for _ in range(5)]
                    accel = (random.uniform(-0.1, 0.1), random.uniform(-0.1, 0.1), 9.8 + random.uniform(-0.1, 0.1))
                    gyro = (random.uniform(-0.01, 0.01), random.uniform(-0.01, 0.01), random.uniform(-0.01, 0.01))
                    mag = (30.0 + random.uniform(-0.5, 0.5), random.uniform(-0.5, 0.5), random.uniform(-0.5, 0.5))
                    bme_data = (1013.25 + random.uniform(-1, 1), 40.0 + random.uniform(-0.5, 0.5), 25.0 + random.uniform(-0.5, 0.5))
                else:
                    accel, gyro, mag = self.imu.get_data()
                    t_data = self.temp.get_all_temps()
                    bme_data = self.bme280.get_data()

                # Timestamp Logic
                current_time = time.time()
                is_utc = 1 if self.is_utc_valid else 0

                # Safety Logic (LED Alert)
                self.temp.set_led_alert(any(t >= 30 for t in t_data))

                # Pack for CCSDS
                print(int(current_time), *t_data, *accel, *gyro, *mag, *bme_data, is_utc)
                payload = struct.pack(">Ifffff fff fff fff fff B", 
                    int(current_time), *t_data, *accel, *gyro, *mag, *bme_data, is_utc)
                
                # Log the data
                self.logger.write(payload)

                # Precise Timing
                elapsed = time.time() - loop_start
                sleep_time = (1.0 / self.sample_rate) - elapsed
                if sleep_time > 0:
                    time.sleep(sleep_time)

        # Handle graceful exit
        except KeyboardInterrupt:
            print("\nCleaning up GPIO...")
            import RPi.GPIO as GPIO
            GPIO.cleanup()

if __name__ == "__main__":
    # Check if "--simulate" was passed in the terminal command
    is_sim = "--simulate" in sys.argv
    
    # Pass that result into your class
    mission = FlightStateMachine(sample_rate=10, simulate=is_sim)
    mission.run()