from helpers.rv8803 import RV8803

def main():
    rtc = RV8803()
    rtc.set_time()
    rtc.sync_system_clock()

if __name__ == '__main__':
    main()