import smbus2
import bme280
import math

class BME280Sensor:
    """
    PURPOSE: Handles BME280 I2C communication and data sampling.
    ERROR HANDLING: If the sensor fails to initialize or read, it returns NaN values instead of crashing the mission loop. This allows the rest of the system to function even if one sensor fails.
    """
    def __init__(self, address=0x77, bus_id=1):
        self.address = address

        # Attempt to initialize the sensor and load calibration parameters
        try:
            self.bus = smbus2.SMBus(bus_id)
            self.calibration_params = bme280.load_calibration_params(self.bus, self.address)
            self.connected = True
        except Exception as e:
            print(f"[BME280 Initialization Error]: Could not connect sensor at {hex(address)}: {e}")
            self.connected = False

    def get_data(self):
        """Returns (temp [C], pressure [hPa], humidity [%]). Returns NaN for all if sensor fails."""
        nan_triple = (float('nan'), float('nan'), float('nan'))
        
        # Return nans if sensor is not connected to avoid crashing the mission loop; this allows the rest of the system to function even if one sensor fails.
        if not self.connected:
            return nan_triple
            
        # Attempt to read data from the sensor, handling any exceptions
        try:
            data = bme280.sample(self.bus, self.address, self.calibration_params)
            return data.temperature, data.pressure, data.humidity
        except Exception as e:
            print(f"[BME280 Data Error]: Failed to read sensor: {e}")
            return nan_triple
