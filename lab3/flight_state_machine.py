import sys
import struct
import os
import time
import random
from unittest.mock import MagicMock

class FlightStateMachine:
    """
    PURPOSE: Coordinates timing, sensor polling, and CCSDS logging.
    REASONING: Controls the "Mission Loop." Can run on a laptop (Simulation) 
               or on the ISS hardware (Flight).
    """
    def __init__(self, sample_rate=10, simulate=True):
        self.simulate = simulate
        self.sample_rate = sample_rate
        self.start_time = time.time()

        if self.simulate:
            self._setup_simulation()
            print("--- INITIALIZED IN SIMULATION MODE ---")
        
        # Now we import our custom classes. 
        # If simulate=True, these classes will find the 'Mocks' in sys.modules
        from imu_sensor import IMUSensor
        from temp_sensors import TempSensor
        from ccsds import CCSDSWriter
        # from spacetime import SpaceTime # Uncomment if using your custom time class

        # Initialize Hardware or Mocks
        self.imu = IMUSensor()
        self.temp = TempSensor()
        
        # Set data folder based on mode
        data_folder = "simulated-data" if self.simulate else "data"
        self.logger = CCSDSWriter(apid=0x123, folder=data_folder)
        
        # Internal time tracking
        self.is_utc_valid = not self.simulate # Laptops usually have UTC; Pis don't always.

    def _setup_simulation(self):
        """Injects fake modules into the system to prevent crashes on laptops."""
        # 1. Define Registers/Constants
        mock_regs = MagicMock()
        mock_regs.AK8963_ADDRESS = 0x0C
        mock_regs.MPU9050_ADDRESS_68 = 0x68
        mock_regs.AK8963_BIT_16 = 0x01
        mock_regs.AK8963_MODE_C100HZ = 0x06
        mock_regs.GFS_1000 = 0x02
        mock_regs.AFS_8G = 0x02

        # 2. Inject Modules
        mocks = ["RPi", "RPi.GPIO", "ADS1x15", "mpu9250_jmdev", 
                 "mpu9250_jmdev.registers", "mpu9250_jmdev.mpu_9250"]
        for module in mocks:
            sys.modules[module] = MagicMock()
        
        # 3. Attach Constants
        sys.modules["mpu9250_jmdev.registers"] = mock_regs
        
        # 4. Define Fake Hardware Classes
        class MockADS:
            def __init__(self, bus, address): self.PGA_4_096V = 4.096
            def setGain(self, gain): pass
            def toVoltage(self): return 0.000125
            def readADC(self, channel): return 16000 + random.randint(-100, 100)

        class MockMPU:
            def __init__(self, **kwargs): pass
            def configure(self): pass
            def readAccelerometerMaster(self): return (0.0, 0.0, 9.8 + random.uniform(-0.1, 0.1))
            def readGyroscopeMaster(self): return (random.uniform(-0.1, 0.1), 0.0, 0.0)
            def readMagnetometerMaster(self): return (45.0, 10.0, -2.0)

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
                t_data = self.temp.get_all_temps()
                accel, gyro, mag = self.imu.get_data()
                if self.simulate:
                    accel = (accel[0], accel[1], 9.8 + random.uniform(-0.1, 0.1))
                    gyro = (gyro[0] + random.uniform(-0.01, 0.01), gyro[1] + random.uniform(-0.01, 0.01), gyro[2] + random.uniform(-0.01, 0.01))
                    mag = (mag[0] + random.uniform(-0.5, 0.5), mag[1] + random.uniform(-0.5, 0.5), mag[2] + random.uniform(-0.5, 0.5))
                
                # Timestamp Logic
                current_time = time.time()
                is_utc = 1 if self.is_utc_valid else 0

                # 2. Safety Logic (LED Alert)
                self.temp.set_led_alert(any(t >= 30 for t in t_data))

                # 3. Pack for CCSDS
                #print(int(current_time), *t_data, *accel, *gyro, *mag, is_utc)
                payload = struct.pack(">Ifffff fff fff fff B", 
                    int(current_time), *t_data, *accel, *gyro, *mag, is_utc)
                
                self.logger.write(payload)

                # 4. Precise Timing
                elapsed = time.time() - loop_start
                sleep_time = (1.0 / self.sample_rate) - elapsed
                if sleep_time > 0:
                    time.sleep(sleep_time)

        except KeyboardInterrupt:
            print("\nCleaning up GPIO...")
            import RPi.GPIO as GPIO
            GPIO.cleanup()

if __name__ == "__main__":
    # Toggle this to False when moving to the Pi
    mission = FlightStateMachine(sample_rate=10, simulate=True)
    mission.run()