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
        weekday = curr_time.isoweekday()

        print(f'Syncing RTC to {curr_time.strftime('%Y-%m-%d %H:%M:%S')}')

        self.rtc.set_time(curr_time.second, curr_time.minute, curr_time.hour, weekday, curr_time.day, curr_time.month, curr_time.year)
        self.rtc._i2c.write_byte(0x32, 0x0E, 0x00)
        print(f'RTC successfully set, time: {self.read_data()}')

    def read_data(self):
        nan = float("nan")
        if not self.connected:
            return nan

        try:
            # update_time() populates self.rtc._time (BCD values)
            self.rtc.update_time()

            # Decode using the same internal mechanism the library uses for string_date_usa/string_time
            year_2 = self.rtc.bcd_to_dec(self.rtc._time[self.rtc.kIdxYear])   # 0..99
            month  = self.rtc.bcd_to_dec(self.rtc._time[self.rtc.kIdxMonth])  # 1..12
            day    = self.rtc.bcd_to_dec(self.rtc._time[self.rtc.kIdxDate])   # 1..31
            hour   = self.rtc.bcd_to_dec(self.rtc._time[self.rtc.kIdxHours])  # 0..23-ish
            minute = self.rtc.bcd_to_dec(self.rtc._time[self.rtc.kIdxMinutes])# 0..59
            second = self.rtc.bcd_to_dec(self.rtc._time[self.rtc.kIdxSeconds])# 0..59

            year = 2000 + year_2

            # Quick validity guard (prevents "day out of range for month")
            if not (1 <= month <= 12 and 1 <= day <= 31 and 0 <= hour <= 23 and 0 <= minute <= 59 and 0 <= second <= 59):
                print(f"[RV8803] Invalid fields: Y={year} M={month} D={day} {hour}:{minute}:{second}")
                return nan

            try:
                dt = datetime(year, month, day, hour, minute, second)
            except ValueError as ve:
                # This catches cases like April 31, Feb 30, day=0, etc.
                print(f"[RV8803] Invalid calendar date from RTC: Y={year} M={month} D={day} ({ve})")
                # Useful debug: show exactly what the library would print
                try:
                    print(f"[RV8803] string_date_usa={self.rtc.string_date_usa()} string_time={self.rtc.string_time()}")
                except Exception:
                    pass
                return nan

            # dt.timestamp() uses local timezone; if you want UTC instead, use calendar/timegm.
            return dt.timestamp()

        except Exception as e:
            print(f"RV8803 read error: {e}")
            return nan

    
    def sync_system_clock(self):
        """Read time from RTC and update the Raspberry Pi OS system time."""
        if not self.connected:
            print("RTC not connected. Cannot sync system clock.")
            return

        # 1. Update the local rtc object with the hardware registers
        if self.rtc.update_time():
            # Get the string (Format: "MM/DD/YYYY HH:MM:SS")
            rtc_time_str = self.rtc.string_date_time
            
            print(f"Syncing System Clock to RTC: {rtc_time_str}")
            
            try:
                # 2. Use subprocess to run the Linux 'date' command
                # Format for date command: "YYYY-MM-DD HH:MM:SS"
                # The RTC string is often "MM/DD/YYYY", so we may need to format it
                subprocess.run(['sudo', 'date', '-s', rtc_time_str], check=True)
                
                # 3. Optional: Sync the hardware clock to the system (if needed)
                # subprocess.run(['sudo', 'hwclock', '-w'], check=True)
                
                print("System clock updated successfully.")
            except subprocess.CalledProcessError as e:
                print(f"Failed to update system clock: {e}")
        else:
            print("Failed to read time from RV8803 hardware.")