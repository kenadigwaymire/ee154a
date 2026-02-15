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
        nan = float('nan')

        if not self.connected:
            return nan
        
        try:
            if self.rtc.update_time():
                return self.rtc.string_date_time
            else:
                return nan
    
        except Exception as e:
            print(f'Some dumb shit happening with RV8803" {e}')
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