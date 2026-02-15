import qwiic_rv8803
import sys
import time
from datetime import datetime

class RV8803:
    """
    PURPOSE: Real time clock 
    ERROR HANDLING: wiener
    """
    
    def __init__(self, address=0x32):
        try:
            self.rtc = qwiic_rv8803.QwiicRV8803()
            if not self.rtc.is_connected:
                print(f'RTC not connected but no exception.')
                self.connected = False
            else:
                self.connected = True
                self.rtc.begin()
        except Exception as e:
            print(f'RTC not connected: {e}')
            self.connected = False

    def set_time(self):

        curr_time = datetime.now()
        weekday = curr_time.isoweekday()

        print(f'Syncing RTC to {curr_time.strftime('%Y-%m-%d %H:%M:%S')}')
        
        success = self.rtc.set_time(curr_time.second, curr_time.minute, curr_time.hour, weekday, curr_time.day, curr_time.month, curr_time.year)
        if success:
            print(f'RTC successfully set, time: {self.read_data()}')
        else:
            print(f'RTC time sync unsuccessful')

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