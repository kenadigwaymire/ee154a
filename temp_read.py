import os
import time
import ADS1x15

# choose your sensor
# ADS = ADS1x15.ADS1013(1, 0x48)
# ADS = ADS1x15.ADS1014(1, 0x48)
# ADS = ADS1x15.ADS1015(1, 0x48)
# ADS = ADS1x15.ADS1113(1, 0x48)
# ADS = ADS1x15.ADS1114(1, 0x48)

ADS1 = ADS1x15.ADS1115(1, 0x48)
ADS2 = ADS1x15.ADS1115(1, 0x49)

print(os.path.basename(__file__))
print("ADS1X15_LIB_VERSION: {}".format(ADS1x15.__version__))

# set gain to 4.096V max
ADS1.setGain(ADS1.PGA_4_096V)
f1 = ADS1.toVoltage()

ADS2.setGain(ADS2.PGA_4_096V)
f2 = ADS2.toVoltage()

while True :
    val_0 = ADS1.readADC(0)
    val_1 = ADS1.readADC(1)
    val_2 = ADS1.readADC(2)
    val_3 = ADS1.readADC(3)
    val_4 = ADS2.readADC(0)
    print("Analog0: {0:d}\t{1:.3f} V".format(val_0, val_0 * f1))
    print("Analog1: {0:d}\t{1:.3f} V".format(val_1, val_1 * f1))
    print("Analog2: {0:d}\t{1:.3f} V".format(val_2, val_2 * f1))
    print("Analog3: {0:d}\t{1:.3f} V".format(val_3, val_3 * f1))
    print("Analog4: {0:d}\t{1:.3f} V".format(val_4, val_4 * f2))

    time.sleep(1)