import os
import time
import ADS1x15
import math

# choose your sensor
# ADS = ADS1x15.ADS1013(1, 0x48)
# ADS = ADS1x15.ADS1014(1, 0x48)
# ADS = ADS1x15.ADS1015(1, 0x48)
# ADS = ADS1x15.ADS1113(1, 0x48)
# ADS = ADS1x15.ADS1114(1, 0x48)

A = 1.02192985237609e-3
B = 2.41453242427025e-4
C = -2.47620754758454e-7
D = 1.65394923419592e-7

R_VAL = 6800
MULT_CONST = 5

ADS1 = ADS1x15.ADS1115(1, 0x48)
ADS2 = ADS1x15.ADS1115(1, 0x49)

print(os.path.basename(__file__))
print("ADS1X15_LIB_VERSION: {}".format(ADS1x15.__version__))

# set gain to 4.096V max
ADS1.setGain(ADS1.PGA_4_096V)
f1 = ADS1.toVoltage()

ADS2.setGain(ADS2.PGA_4_096V)
f2 = ADS2.toVoltage()

def calc_temp(res):
    inv = A + (B * math.log(res)) + (C * (math.log(res))**2) + (D * (math.log(res))**3)
    return 1/inv

while True :
    val_0 = ADS1.readADC(0)
    val_1 = ADS1.readADC(1)
    val_2 = ADS1.readADC(2)
    val_3 = ADS1.readADC(3)
    val_4 = ADS2.readADC(0)

    v_0 = val_0 * f1
    v_1 = val_1 * f1
    v_2 = val_2 * f1
    v_3 = val_3 * f1
    v_4 = val_4 * f2

    r_0 = ((R_VAL * MULT_CONST) / v_0) - R_VAL
    r_1 = ((R_VAL * MULT_CONST) / v_1) - R_VAL
    r_2 = ((R_VAL * MULT_CONST) / v_2) - R_VAL
    r_3 = ((R_VAL * MULT_CONST) / v_3) - R_VAL
    r_4 = ((R_VAL * MULT_CONST) / v_4) - R_VAL

    t_0 = calc_temp(r_0)
    t_1 = calc_temp(r_1)
    t_2 = calc_temp(r_2)
    t_3 = calc_temp(r_3)
    t_4 = calc_temp(r_4)

    #print("Analog0: {0:d}\t{1:.3f} V".format(val_0, val_0 * f1))
    #print("Analog1: {0:d}\t{1:.3f} V".format(val_1, val_1 * f1))
    #print("Analog2: {0:d}\t{1:.3f} V".format(val_2, val_2 * f1))
    #print("Analog3: {0:d}\t{1:.3f} V".format(val_3, val_3 * f1))
    #print("Analog4: {0:d}\t{1:.3f} V".format(val_4, val_4 * f2))
    print(f"Analog0: {t_0} C")
    print(f"Analog1: {t_0} C")
    print(f"Analog2: {t_0} C")
    print(f"Analog3: {t_0} C")
    print(f"Analog4: {t_0} C")

    time.sleep(1)