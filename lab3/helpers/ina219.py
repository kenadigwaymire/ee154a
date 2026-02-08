from ina219 import INA219
from ina219 import DeviceRangeError

SHUNT_OHMS = 0.1

class INA219Sensor:
    def __init__(self, address=0x40, busnum=1):
        self.ina = INA219(SHUNT_OHMS, address=address, busnum=busnum)
        self.ina.configure()

    def read_data(self):
        try:
            return self.ina.current(), self.ina.power(), self.ina.shunt_voltage()
        except DeviceRangeError:
            return 0.0, 0.0, 0.0
        except Exception as e:
            print(f'INA 219 error: {e}')
            return 0.0, 0.0, 0.0