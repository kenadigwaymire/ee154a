"""
-------------------------------------------------------------------------------
Project: Script to Set RTC Time on RV8803

File:    set_rtc_time.py

Purpose: Sets the real-time clock (RTC) on an RV8803 chip using system time.
         Synchronizes the system clock with the RTC.

Logic: 1. Initializes the RV8803 RTC module.
       2. Sets the RTC time to the current system time.

-------------------------------------------------------------------------------
Author:  James Scott
Date:    February 2026
-------------------------------------------------------------------------------
"""

from helpers.rv8803 import RV8803

def main():
    rtc = RV8803()
    rtc.set_time()
    rtc.sync_system_clock()

if __name__ == '__main__':
    main()