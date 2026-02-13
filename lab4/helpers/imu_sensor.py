from mpu9250_jmdev.registers import *
from mpu9250_jmdev.mpu_9250 import MPU9250

class IMUSensor:
    """
    PURPOSE: Manages the MPU9250 IMU.
    REASONING: Encapsulating the I2C configuration keeps the main loop clean.
    """
    def __init__(self):
        try:
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
            self.connected = True
        except Exception as e:
            print(f"[IMU Initialization Error]: {e}")
            self.connected = False

    def get_data(self):
        """Returns (accel [g], gyro [dps], mag[micro Tesla]) tuples."""
        nan_triple = (float('nan'), float('nan'), float('nan'))
        
        # Dont read data if sensor isnt connected
        if not self.connected:
            return nan_triple, nan_triple, nan_triple

        try: 
            # Pull data       
            accel = self.sensor.readAccelerometerMaster()
            gyro = self.sensor.readGyroscopeMaster()
            mag = self.sensor.readMagnetometerMaster()

            # Handle None or epmty cases (default to NaN)
            if accel is None: 
                accel = nan_triple
                print(f"Accelerometer reading None, defaulting to NaN")
            if gyro is None: 
                gyro = nan_triple
                print(f"Gyroscope reading None, defaulting to NaN")
            if mag is None: 
                mag = nan_triple
                print(f"Magnetometer reading None, defaulting to NaN")        
        
        except Exception as e:
            print(f"[IMU Data Error]: Could not read sensor data: {e}")
            accel, gyro, mag = nan_triple, nan_triple, nan_triple
        
        return (accel, gyro, mag)