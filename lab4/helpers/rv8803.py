"""
-------------------------------------------------------------------------------
Project: Real Time Clock Class for High-Altitude Balloon Mission

File:    rv8803.py

Purpose: Handles reading and processing time data from the RV8803 RTC.
         Provides a clean interface for setting and reading RTC time.

Logic:   1. Initializes the RV8803 RTC and sets up I2C communication.
         2. Sets the RTC time to the system time.
         3. Reads and returns the current RTC time in epoch format.
         4. Synchronizes the system clock with the RTC.

If run as main:
         1. Nothing yet (Could add standalone testing later)
-------------------------------------------------------------------------------
Author:  Kenadi Waymire
Date:    February 2026
-------------------------------------------------------------------------------
"""

import qwiic_rv8803
import sys
import time
from datetime import datetime
import subprocess

class RV8803:
    """
    PURPOSE: Real time clock 
    ERROR HANDLING: wiener
    """
    
    def __init__(self, address=0x32):
        try:
            self.rtc = qwiic_rv8803.QwiicRV8803()
            if not self.rtc.begin():
                print(f'RTC not connected but no exception.')
                self.connected = False
            else:
                self.rtc._i2c.write_byte(0x32, 0x0E, 0x00)
                self.rtc.update_time()
                self.connected = True
        except Exception as e:
            print(f'RTC not connected: {e}')
            self.connected = False

    def set_time(self):

        print('dumb')

        if self.connected:
            print('Why the fuck arent you doing anything dumbass')

        curr_time = datetime.now()
        wd = curr_time.weekday()

        weekday_map = {
            0: self.rtc.kMonday,
            1: self.rtc.kTuesday,
            2: self.rtc.kWednesday,
            3: self.rtc.kThursday,
            4: self.rtc.kFriday,
            5: self.rtc.kSaturday,
            6: self.rtc.kSunday,
        }

        weekday = weekday_map[wd]


        print(f'Syncing RTC to {curr_time.strftime('%Y-%m-%d %H:%M:%S')}')

        self.rtc.set_time(curr_time.second, curr_time.minute, curr_time.hour, weekday, curr_time.day, curr_time.month, curr_time.year)
        self.rtc._i2c.write_byte(0x32, 0x0E, 0x00)
        print(f'RTC successfully set, time: {self.read_data()}')

    def read_data(self):
        nan = float('nan')

        if not self.connected:
            return nan
        
        try:
            self.rtc.update_time()
            return self.rtc.get_epoch()
        
        except Exception as e:
            print(f'RV8803 read error: {e}')
            return nan

    
    def sync_system_clock(self):
        nan = float('nan')

        if not self.connected:
            print("RTC not connected. Cannot sync system clock.")
            return nan

        try:
            self.rtc.update_time()

            rtc_iso = self.rtc.string_time_8601().replace('T', ' ')

            if not rtc_iso or rtc_iso != rtc_iso:
                print("RV8803 read error: got invalid time string.")
                return nan

            rtc_for_date = rtc_iso.replace('T', ' ').split('.')[0]

            #print(f"Syncing System Clock to RTC: {rtc_for_date}")

            #subprocess.run(['sudo', 'date', '-s', rtc_for_date], check=True)

            #print("System clock updated successfully.")
            return rtc_iso

        except Exception as e:
            print(f"RV8803 read error: {e}")
            return nan
