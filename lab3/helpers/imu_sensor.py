from mpu9250_jmdev.registers import *
from mpu9250_jmdev.mpu_9250 import MPU9250

class IMUSensor:
    """
    PURPOSE: Manages the MPU9250 IMU.
    REASONING: Encapsulating the I2C configuration keeps the main loop clean.
    """
    def __init__(self):
        self.sensor = MPU9250(
            address_ak=AK8963_ADDRESS,
            address_mpu_master=MPU9050_ADDRESS_68,
            address_mpu_slave=None,
            bus=1,
            gfs=GFS_1000,
            afs=AFS_8G,
            mfs=AK8963_BIT_16,
            mode=AK8963_MODE_C100HZ)
        self.sensor.configure()

    def get_data(self):
        """Returns (accel, gyro, mag) tuples."""
        accel = self.sensor.readAccelerometerMaster()
        gyro = self.sensor.readGyroscopeMaster()
        mag = self.sensor.readMagnetometerMaster()
        return accel, gyro, mag