import smbus2
import bme280
import math

class BME280Sensor:
    """
    PURPOSE: Handles BME280 I2C communication and data sampling.
    ERROR HANDLING: If the sensor fails to initialize or read, it returns NaN values instead of crashing the mission loop. This allows the rest of the system to function even if one sensor fails.
    """

    SEA_LEVEL_PRESSURE_HPA = 1013.25
    CONST_FT = 145442
    CONST_M = 44330
    EXP_CONST = 0.1903

    def __init__(self, address=0x77, bus_id=1):
        self.address = address
        self.temp = 0
        self.pressure = 0
        self.humidity = 0

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
        nan = float('nan')
        
        # Return nans if sensor is not connected to avoid crashing the mission loop; this allows the rest of the system to function even if one sensor fails.
        if not self.connected:
            return (nan, nan, nan)
            
        # Attempt to read data from the sensor, handling any exceptions
        try:
            data = bme280.sample(self.bus, self.address, self.calibration_params)
            temp = data.temperature
            self.temp = temp
            pressure = data.pressure
            self.pressure = pressure
            humidity = data.humidity
            self.humidity = humidity
            
            if temp is None:
                print(f"BME280 temperature reading None, defaulting to NaN")
                temp = nan
            if pressure is None:
                print(f"BME280 pressure reading None, defaulting to NaN")
                pressure = nan
            if humidity is None:
                print(f"BME280 humidity reading None, defaulting to NaN")
                humidity = nan

            return temp, pressure, humidity
        
        except Exception as e:
            print(f"[BME280 Data Error]: Failed to read sensor: {e}")
            return (nan, nan, nan)
        
    def calculate_altitude_ft(self):
        nan = float('nan')
        try: 
            return self.CONST_FT * (1 - ((self.pressure / self.SEA_LEVEL_PRESSURE_HPA) ** self.EXP_CONST))
        except Exception as e:
            print(f'Some sensor being stupid: {e}')
            return nan
    
    def calculate_altitude_m(self):
        nan = float('nan')
        try:
            return self.CONST_M * (1 - ((self.pressure / self.SEA_LEVEL_PRESSURE_HPA) ** self.EXP_CONST))
        except Exception as e:
            print(f'Some sensor being stupid: {e}')
            return nan
