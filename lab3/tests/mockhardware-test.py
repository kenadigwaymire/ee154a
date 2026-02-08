import sys
from unittest.mock import MagicMock

# 1. DEFINE MOCK CLASSES
# We need actual classes for the things your code tries to 'initialize' (like MPU9250())
class MockMPU:
    def __init__(self, **kwargs): pass
    def configure(self): pass
    def readAccelerometerMaster(self): return (0.0, 0.0, 9.8)
    def readGyroscopeMaster(self): return (0.0, 0.0, 0.0)
    def readMagnetometerMaster(self): return (0.0, 0.0, 0.0)

class MockADS:
    def __init__(self, bus, address): 
        self.PGA_4_096V = 4.096
    def setGain(self, gain): pass
    def toVoltage(self): return 1.0
    def readADC(self, channel): return 1000 # Fake ADC counts

# 2. POPULATE SYS.MODULES
# This "tricks" Python into thinking these libraries are installed.
mock_modules = {
    "RPi": MagicMock(),
    "RPi.GPIO": MagicMock(),
    "ADS1x15": MagicMock(),
    "mpu9250_jmdev": MagicMock(),
    "mpu9250_jmdev.registers": MagicMock(),
    "mpu9250_jmdev.mpu_9250": MagicMock(),
}

# Inject the mocks into the system
for name, m in mock_modules.items():
    sys.modules[name] = m

# 3. ATTACH THE CLASSES AND CONSTANTS
# Your code expects 'ADS1x15.ADS1115', so we attach our Mock class to the Mock module.
import ADS1x15
ADS1x15.ADS1115 = MockADS

import mpu9250_jmdev.mpu_9250
mpu9250_jmdev.mpu_9250.MPU9250 = MockMPU

# Set up GPIO constants so setup() calls don't crash
import RPi.GPIO as GPIO
GPIO.BCM = 11
GPIO.OUT = 1
GPIO.HIGH = 1
GPIO.LOW = 0

print("--- RUNNING IN LAPTOP SIMULATION MODE ---")