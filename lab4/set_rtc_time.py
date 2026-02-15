from helpers.rv8803 import RV8803

def main():
    rtc = RV8803()
    rtc.set_time()

if __name__ == 'main':
    main()