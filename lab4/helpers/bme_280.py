import smbus2
import bme280

class BME280Sensor:
    """
    PURPOSE: Handles BME280 I2C communication and data sampling.
    """
    def __init__(self, address=0x77, bus_id=1):
        self.address = address
        try:
            self.bus = smbus2.SMBus(bus_id)
            self.calibration_params = bme280.load_calibration_params(self.bus, self.address)
            self.connected = True
        except Exception as e:
            print(f"[BME280 ERROR]: Could not initialize sensor at {hex(address)}: {e}")
            self.connected = False

    def get_data(self):
        """Returns (temp_c, pressure, humidity). Returns zeros if sensor fails."""
        if not self.connected:
            return 0.0, 0.0, 0.0
            
        try:
            data = bme280.sample(self.bus, self.address, self.calibration_params)
            return data.temperature, data.pressure, data.humidity
        except Exception as e:
            print(f"[BME280 ERROR]: Failed to read sensor: {e}")
            return 0.0, 0.0, 0.0

    @staticmethod
    def c_to_f(celsius):
        return (celsius * 9/5) + 32