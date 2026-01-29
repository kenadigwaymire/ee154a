# main.py

# Standard library imports
import os
import time
import math
import csv

# MPU9250 sensor imports
from mpu9250_jmdev.registers import *
from mpu9250_jmdev.mpu_9250 import MPU9250

# Temp sensor imports
import ADS1x15

class Main:
    def __init__(self):
        # Setup IMU
        self.imu = MPU9250(
            address_ak=AK8963_ADDRESS,
            address_mpu_master=MPU9050_ADDRESS_68,  # In case the MPU9250 is connected to another I2C device
            address_mpu_slave=None,
            bus=1,
            gfs=GFS_1000,
            afs=AFS_8G,
            mfs=AK8963_BIT_16,
            mode=AK8963_MODE_C100HZ)
        self.imu.configure()

        #Setup Temp Variables
        self.ADS1 = ADS1x15.ADS1115(1, 0x49)
        self.ADS2 = ADS1x15.ADS1115(1, 0x48)
        self.A = 1.02192985237609e-3
        self.B = 2.41453242427025e-4
        self.C = -2.47620754758454e-7
        self.D = 1.65394923419592e-7
        self.R_VAL = 6800
        self.VCC = 3.3

        # Define speed
        self.sample_rate_hz = 10
        self.last_sample_time = time.time()

    def getImuData(self):
        accel_data = self.imu.readAccelerometerMaster()
        gyro_data = self.imu.readGyroscopeMaster()
        mag_data = self.imu.readMagnetometerMaster()
        return accel_data, gyro_data, mag_data

    def calcTemperature(self, res):
            inv = self.A + (self.B * math.log(res)) + (self.C * (math.log(res))**2) + (self.D * (math.log(res))**3)
            return 1/inv - 273.15
    
    def getTempData(self):
        # set gain to 4.096V max
        self.ADS1.setGain(self.ADS1.PGA_4_096V)
        f1 = self.ADS1.toVoltage()

        self.ADS2.setGain(self.ADS2.PGA_4_096V)
        f2 = self.ADS2.toVoltage()

        val_0 = self.ADS1.readADC(0)
        val_1 = self.ADS1.readADC(1)
        val_2 = self.ADS1.readADC(2)
        val_3 = self.ADS1.readADC(3)
        val_4 = self.ADS2.readADC(1)

        v_0 = val_0 * f1
        v_1 = val_1 * f1
        v_2 = val_2 * f1
        v_3 = val_3 * f1
        v_4 = val_4 * f2

        r_0 = ((self.R_VAL * self.VCC) / v_0) - self.R_VAL
        r_1 = ((self.R_VAL * self.VCC) / v_1) - self.R_VAL
        r_2 = ((self.R_VAL * self.VCC) / v_2) - self.R_VAL
        r_3 = ((self.R_VAL * self.VCC) / v_3) - self.R_VAL
        r_4 = ((self.R_VAL * self.VCC) / v_4) - self.R_VAL

        t_0 = self.calcTemperature(r_0)
        t_1 = self.calcTemperature(r_1)
        t_2 = self.calcTemperature(r_2)
        t_3 = self.calcTemperature(r_3)
        t_4 = self.calcTemperature(r_4)

        return t_0, t_1, t_2, t_3, t_4
    
    def recordData(self):
        headers = [
        ['ABS TIME', 
        'T1', 'T2', 'T3', 'T4', 'T5', 
        'X ACC', 'Y ACC', 'Z ACC', 
        'X GYRO', 'Y GYRO', 'Z GYRO', 
        'X MAG', 'Y MAG', 'Z MAG',]]

        with open('lab2.csv', 'w', newline='') as csvfile:
            writer = csv.writer(csvfile, delimiter='|')
            writer.writerows(headers)

            while True:

                # Wait until it's time for the next sample
                while time.time() - self.last_sample_time < (1 / self.sample_rate_hz):
                    # Do nothing
                    pass
                # Reset the sample time
                self.last_sample_time = time.time()

                # Read data from sensors
                T1, T2, T3, T4, T5 = self.getTempData()

                accel_data, gyro_data, mag_data = self.getImuData()
                X_ACC, Y_ACC, Z_ACC = accel_data
                X_GYRO, Y_GYRO, Z_GYRO = gyro_data
                X_MAG, Y_MAG, Z_MAG = mag_data

                # Print data as we go
                t = time.time()
                print(f"time: {t:.2f}, T1: {T1:.2f}, T2: {T2:.2f}, T3: {T3:.2f}, T4: {T4:.2f}, T5: {T5:.2f}")
                
                # Save data to CSV
                data = [[t, 
                        T1, T2, T3, T4, T5, 
                        X_ACC, Y_ACC, Z_ACC, 
                        X_GYRO, Y_GYRO, Z_GYRO, 
                        X_MAG, Y_MAG, Z_MAG]]
                
                writer.writerows(data)

main = Main()
main.recordData()

