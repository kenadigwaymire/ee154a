import serial
import pynmea2
import time

class GP3906:

    PORT = "/dev/serial0"
    BAUD_RATE = 9600
    TIMEOUT = 0.5

    def __init__(self):
        try:
            self.ser = serial.Serial(self.PORT, baudrate=self.BAUD_RATE, timeout=self.TIMEOUT)
            print(f'GP3906 intialized on port {self.PORT}')
            self.connected = True
        except Exception as e:
            print(f'Failed to connect to GP3906: {e}')
            self.connected = False
            self.ser = None

    def read_data(self):
        nan = float('nan')

        if not self.ser:
            return nan, nan, nan
        
        try:
            line = self.ser.readline.decode('ascii', errors='replace').strip()
            # with altitude
            if line.startswith('$GPGGA'):
                msg = pynmea2.parse(line)

                if msg.gps_qual > 0:
                    latitude = msg.latitude
                    longitude = msg.longitude
                    altitude = msg.altitude
                    return latitude, longitude, altitude
                
            # without altitude
            elif line.startswith('$GPRMC'):
                msg = pynmea2.parse(line)

                if msg.status == 'A':
                    latitude = msg.latitude
                    longitude = msg.longitude
                    altitude = nan
                    return latitude, longitude, altitude
        
        except pynmea2.ParseError:
            pass # ignore fucked up lines
        
        except Exception as e:
            print(f'GPS doing some dumb shit: {e}')
        
        return nan, nan, nan