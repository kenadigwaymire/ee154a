from ina219 import INA219
from ina219 import DeviceRangeError

# SHUNT_OHMS is the resistance of the shunt resistor used in the INA219 sensor. 
SHUNT_OHMS = 0.1

class INA219Sensor:
    def __init__(self, address=0x40, busnum=1):
        try:
            self.ina = INA219(SHUNT_OHMS, address=address, busnum=busnum)
            self.ina.configure()
            self.connected = True
        except Exception as e:
            print(f"INA219 initialization error: {e}")
            self.ina = None
            self.connected = False

    def read_data(self):
        nan = float('nan')
        
        if not self.connected:
            return nan, nan, nan

        try:
            curr = self.ina.current()
            power = self.ina.power()
            voltage = self.ina.voltage()

            if curr is None :
                print(f"INA219 current reading None, defaulting to NaN")
                curr = nan
            if power is None :
                print(f"INA219 power reading None, defaulting to NaN")
                power = nan
            if voltage is None :
                print(f"INA219 voltage reading None, defaulting to NaN")
                voltage = nan

            return voltage, curr, power
        
        except DeviceRangeError as e:
            print(f"INA219 DeviceRangeError: {e}")
            return nan, nan, nan
    
        except Exception as e:
            print(f'INA 219 data error: {e}')
            return nan, nan, nan