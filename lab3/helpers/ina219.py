from ina219 import INA219
from ina219 import DeviceRangeError

SHUNT_OHMS = 0.1

class INA219Sensor:
    def __init__(self):
        self.ina = INA219(SHUNT_OHMS, address = 0x41)
        self.ina.configure()

    def read_data(self):
        try:
            return self.ina.current(), self.ina.power(), self.ina.shunt_voltage()
        except DeviceRangeError as e:
            return 0.0, 0.0, 0.0