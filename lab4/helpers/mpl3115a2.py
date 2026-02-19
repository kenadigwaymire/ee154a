"""
-------------------------------------------------------------------------------
Project: Altitude Sensor Class for High-Altitude Balloon Mission

File:    mpl3115a2.py

Purpose: Handles reading and processing altitude data from the MPL3115A2 sensor.
         Provides a clean interface for reading altitude in feet.

Logic:   1. Initializes the MPL3115A2 sensor and sets up I2C communication.
         2. Sets the sensor to the correct operating mode.
         3. Reads and returns the current altitude in feet.

If run as main:
         1. Nothing yet (Could add standalone testing later)
-------------------------------------------------------------------------------
Author:  Kenadi Waymire
Date:    February 2026
-------------------------------------------------------------------------------
"""

import smbus2
import time 

class MPL3115A2:
    
    CONTROL_REG = 0x26
    OSR_128_REG = 0xB9
    DEVICE_ID_REG = 0x0C
    DEVICE_ID_DES = 0xC4

    DATA_REG = 0x01
    NUM_REG = 5
    MAX_ALT = 524287
    OFFSET = 1048576
    FT_CONV = 3.28084


    def __init__(self, address=0x60):
        self.address = address
        self.bus = smbus2.SMBus(1)
        try:
            device_id = self.bus.read_byte_data(address, self.DEVICE_ID_REG)
            if device_id == self.DEVICE_ID_DES:
                print(f'MPL3115A2 detected with correct device ID!')
                self.bus.write_byte_data(address, self.CONTROL_REG, self.OSR_128_REG)
                time.sleep(0.1)
            else:
                print(f'MPL3115A2 but device ID is incorrect, check connections/sensor.')
                self.connected = False
            self.connected = True
        except Exception as e:
            print(f'{e}: No device found at 0x{address:x}, check wiring and power.')
            self.connected = False
        
    def read_data(self):
        nan = float('nan')

        if not self.connected:
            return nan
        
        try: 
            data = self.bus.read_i2c_block_data(self.address, self.DATA_REG, self.NUM_REG)
            altitude = ((data[0] << 16) | (data[1] << 8) | data[2]) >> 4
            if not altitude:
                print(f'Altitude doing some dumb shit, defaulting to NaN')
                return nan
            if altitude > self.MAX_ALT:
                altitude -= self.OFFSET
            altitude_ft = (altitude / 16.0) * self.FT_CONV
            return altitude_ft
        
        except Exception as e:
            print(f'Something fucked up with the MPL3115A2: {e}')
            return nan
        
