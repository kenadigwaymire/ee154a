"""
-------------------------------------------------------------------------------
Project: GPS Class for High-Altitude Balloon Mission

File:    gp3906.py

Purpose: Handles reading and processing GPS data from a serial connection.
         Provides a clean interface for reading latitude, longitude, and altitude.

Logic:   1. Initializes the serial connection to the GPS module.
         2. Reads and parses NMEA sentences to extract GPS data.
         3. Handles errors gracefully and returns NaN for invalid readings.

If run as main:
         1. Continuously reads GPS data and prints it in a user-friendly format.
         2. Handles keyboard interrupt to exit gracefully.
-------------------------------------------------------------------------------
Author:  James Scott and Kenadi Waymire
Date:    February 2026
-------------------------------------------------------------------------------
"""

import sys
import serial
import pynmea2
import time
import math 

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
            line = self.ser.readline().decode('ascii', errors='replace').strip()
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
    
if __name__ == "__main__":
    gps = GP3906()
    
    if not gps.connected:
        print("Exiting: Could not open serial port. Check your UART settings/Bluetooth.")
        sys.exit(1)

    print("--- Starting GPS Test ---")
    print("Note: If the LED is blinking, we expect NaN, but we should still see raw data.")
    print("Press Ctrl+C to stop.\n")

    try:
        while True:
            # 1. Test the raw serial connection first
            if gps.ser.in_waiting > 0:
                raw_line = gps.ser.readline().decode('ascii', errors='replace').strip()
                print(f"RAW: {raw_line}")
                
                # 2. Test the class logic
                # We have to 'manually' feed logic if we want to test parsing,
                # but let's just use your existing read_data function:
                lat, lon, alt = gps.read_data()
                
                if any(not math.isnan(val) for val in [lat, lon, alt]): # Check if any value is valid
                    print(f"  --> LOCK ACQUIRED! Lat: {lat}, Lon: {lon}, Alt: {alt}")
                else:
                    print("  --> No lock yet (Searching for satellites...)")
            
            time.sleep(0.1)
            
    except KeyboardInterrupt:
        print("\nTest stopped by user.")
    finally:
        if gps.ser:
            gps.ser.close()