"""
-------------------------------------------------------------------------------
Project: Flight Raspberry Pi Data Acquisition (DAQ)

File:    flight-state-machine.py

Purpose: Orchestrates the primary mission loop for a high-altitude balloon.
         Coordinates sensor polling (IMU, BME280, GPS, etc.),
         CCSDS-compliant binary logging, time synchronization via RTC, and
         automated camera/video recording.

Logic:   Implements a state machine to handle sensor re-initialization,
         graceful shutdowns via signal interrupts, and timing-critical
         measurement intervals.
-------------------------------------------------------------------------------
Author:  James Scott & Kenadi Waymire
Date:    February 2026
-------------------------------------------------------------------------------
"""

# Standard Library Imports (Some packages imported within class methods, but others required globally)
import sys
import struct
import os
import time
import random
import smbus2
import bme280
import signal
import datetime
import math


def service_shutdown(signum, frame):
    """
    Terminates program safely incase of watchdog timeout or manual interrupt (Ctrl+C). Ensures GPIO cleanup and resource release.

    Args:
        signum (int): The signal number that triggered the shutdown (e.g., SIGTERM, SIGINT).
        frame: The current stack frame (not used in this function but required by the signal handler signature).

    Raises:
        KeyboardInterrupt: This is raised to signal the main loop to perform cleanup and exit gracefully.
    """
    print(f"Caught signal {signum}. Shutting down mission...")
    raise KeyboardInterrupt


class FlightStateMachine:
    """
    Class to manage the state of the flight mission, including sensor polling, data logging, and camera control.
    Runs the main mission loop, ensuring that data is collected at the specified sample rate and that sensors are re-initialized if they fail. Also handles graceful shutdown on interrupt signals.
    """

    def __init__(self, sample_rate=10):
        """
        Initializes the FlightStateMachine with the specified sample rate and sets up initial states for sensors and camera.

        Args:
            sample_rate (int): The rate at which to collect data from sensors (in Hz).
        """
        # Initialize timing variables
        self.curr_time = time.time()            # Current time in seconds since the epoch; used for synchronized timing across the mission
        
        # Data sampling
        self.sample_rate = sample_rate          # Hz at which we collect data
        self.start_time = self.curr_time        # Zeroes the mission time to when the class is instantiated
        self.loop_start = self.curr_time - (1.0 / self.sample_rate)

        # Camera settings (General)
        self.camera_mode = "video" # "photo" or "video"; adjust as needed. In "photo" mode, it will take photos at the defined camera_rate. In "video" mode, it will record videos of defined duration.


        # Photo settings
        self.photo_rate = 1 / 60                                        # Hz (1 photo per minute); adjust as needed 
        self.last_photo_time = self.curr_time - (1.0 / self.photo_rate) # Time when the last photo was taken; initialized to allow immediate capture on mission start if camera is connected and in photo mode

        # Video settings
        self.video_duration = 10                # sec
        self.video_active = False               # Whether we're currently recording video
        self.last_video_time = self.curr_time   # Time when the current video recording started; used to determine when to stop recording based on duration

        # LED settings
        self.led_flash_dur = 1.0                # sec
        self.last_led_flash = self.curr_time    # Time of the last LED flash; used to control flashing intervals

        # Path to store CCSDS data files; ensure this folder exists on your Raspberry Pi before running the mission
        self.data_folder = "data"

        # Initial sensor statuses (0 = not connected/failed, 1 = connected/working)
        self.bme280_status = 0
        self.ina219_status = 0
        self.imu_status = 0
        self.temp_status = 0
        self.mpl_status = 0
        self.gps_status = 0
        self.rtc_status = 0
        self.led_status = 0
        self.camera_status = 0

        # Reinitialization settings
        self.reinit_dur = 30.0              # seconds
        self.last_reinit = self.curr_time   # Time of the last sensor reinitialization attempt

        # Initialize hardware and sensors
        self.import_hardware()      # Import classes
        self.logger_init()          # Initialize CCSDS logger
        self.initialize_sensors()   # Attempt to initialize all sensors; will set status flags accordingly

    def import_hardware(self):
        """
        Attempts to import all necessary hardware libraries for the sensors and camera. 
        If any imports fail, it prints an error message and exits the program, as the 
        mission cannot run without these components.

        Raises:
            ImportError: If any of the required hardware libraries cannot be imported, 
            an error message is printed and the program exits.
        """
        try:
            from helpers.imu_sensor import IMUSensor
            from helpers.temp_sensors import TempSensor
            
            from helpers.bme_280 import BME280Sensor
            from helpers.ina219 import INA219Sensor
            from helpers.camera import HQCameraRecorder
            from helpers.mpl3115a2 import MPL3115A2
            from helpers.led import LEDIndicator
            from helpers.rv8803 import RV8803
            from helpers.gp3906 import GP3906

        except ImportError as e:
            print(f"Error importing hardware libraries: {e}")
            print(
                "Make sure you're running this on a Raspberry Pi with the required libraries installed."
            )
            sys.exit(1)

    def logger_init(self):
        """
        Attempts to initialize the CCSDS logger for data recording. If the logger 
        cannot be initialized, it prints an error message and exits the program, as 
        data logging is a critical component of the mission.

        Raises:
            Exception: If the CCSDSWriter cannot be initialized, an error message 
            is printed and the program exits.
        """
        try:
            from helpers.ccsds import CCSDSWriter
            self.logger = CCSDSWriter(apid=0x123, folder=self.data_folder)
        except Exception as e:
            print(e)
            sys.exit(1)

    def camera_init(self):
        """
        Attempts to initialize the camera for photo and video recording. 
        If the camera cannot be initialized (e.g., not connected), it 
        sets the camera status to 0 and prints a warning message, but 
        allows the mission to continue without imaging capabilities.
        
        Raises:
            Exception: If the camera cannot be initialized, a warning 
            message is printed, but the program continues to run 
            without the camera.
        """
        try:
            from helpers.camera import HQCameraRecorder
            self.camera = HQCameraRecorder()
            self.camera.setup_camera(mode=self.camera_mode)
            self.camera_connected = True
            print("Camera initialized successfully.")
        except Exception as e:
            self.camera_connected = False
            self.camera = (
                None  # Set to None so we don't try to call methods on it
            )
            print(f"\n[WARNING] Camera not found or unplugged: {e}")
            print("Mission will continue without imaging.")

    def imu_init(self):
        """
        Attempts to initialize the IMU sensor for motion data collection.
        
        Raises:
            Exception: If the IMU sensor cannot be initialized, an error 
            message is printed.
        """
        try:
            from helpers.imu_sensor import IMUSensor
            self.imu = IMUSensor()
        except Exception as e:
            self.imu = None
            print(e)

    def temp_init(self):
        """
        Attempts to initialize the temperature sensors for thermal data collection.
        
        Raises:
            Exception: If the temperature sensors cannot be initialized, 
            an error message is printed.
        """
        try:
            from helpers.temp_sensors import TempSensor
            self.temp = TempSensor()
        except Exception as e:
            self.temp = None
            print(e)

    def bme280_init(self):
        """
        Attempts to initialize the BME280 sensor for environmental data collection.
        
        Raises:
            Exception: If the BME280 sensor cannot be initialized, an error message is printed.
        """
        try:
            from helpers.bme_280 import BME280Sensor
            self.bme280 = BME280Sensor()
        except Exception as e:
            self.bme280 = None
            print(e)

    def ina_init(self):
        """
        Attempts to initialize the INA219 sensor for power monitoring data collection.
        
        Raises:
            Exception: If the INA219 sensor cannot be initialized, an error message is printed."""
        try:
            from helpers.ina219 import INA219Sensor
            self.ina219 = INA219Sensor()
        except Exception as e:
            self.ina219 = None
            print(e)

    def mpl_init(self):
        """
        Attempts to initialize the MPL3115A2 sensor for altitude and pressure data collection.
        
        Raises:
            Exception: If the MPL3115A2 sensor cannot be initialized, an error message is printed.
        """
        try:
            from helpers.mpl3115a2 import MPL3115A2
            self.mpl = MPL3115A2()
        except Exception as e:
            self.mpl = None
            print(e)

    def led_init(self):
        """
        Attempts to initialize the LED indicator for visual status feedback.
        
        Raises:
            Exception: If the LED indicator cannot be initialized, an error message is printed.
        """
        try:
            from helpers.led import LEDIndicator

            self.led = LEDIndicator()
        except Exception as e:
            self.led = None
            print(e)

    def gps_init(self):
        """
        Attempts to initialize the GPS module for location data collection.
        
        Raises:
            Exception: If the GPS module cannot be initialized, an error message is printed.
        """
        try:
            from helpers.gp3906 import GP3906
            self.gps = GP3906()
        except Exception as e:
            self.gps = None
            print(e)

    def rtc_init(self):
        """
        Attempts to initialize the RTC module for time synchronization.

        Raises:
            Exception: If the RTC module cannot be initialized, an error message is printed.
        """
        try:
            from helpers.rv8803 import RV8803
            self.rtc = RV8803()
        except Exception as e:
            self.rtc = None
            print(e)

    def initialize_sensors(self):
        """
        Attempts to initialize all sensors and the camera. If any sensor fails 
        to initialize, it sets the corresponding status flag to 0 and prints 
        an error message, but allows the mission to continue with whatever 
        sensors are available.
        
        Raises:
            Exception: If any sensor fails to initialize, an error message is 
            printed, but the program continues to run with the available sensors.
        """
        if not self.camera_status:
            self.camera_init()
            if self.camera:
                self.camera_status = 1

        if not self.imu_status:
            self.imu_init()
            if self.imu:
                self.imu_status = 1

        if not self.temp_status:
            self.temp_init()
            if self.temp:
                self.temp_status = 1

        if not self.bme280_status:
            self.bme280_init()
            if self.bme280:
                self.bme280_status = 1
        if not self.ina219_status:
            self.ina_init()
            if self.ina219:
                self.ina219_status = 1
        if not self.mpl_status:
            self.mpl_init()
            if self.mpl:
                self.mpl_status = 1
        if not self.led_status:
            self.led_init()
            if self.led:
                self.led_status = 1
        if not self.gps_status:
            self.gps_init()
            if self.gps:
                self.gps_status = 1
        if not self.rtc_status:
            self.rtc_init()
            if self.rtc:
                self.rtc_status = 1

    def handle_time_sync(self):
        """
        Handles time synchronization using the RTC module. If the RTC 
        is connected and provides a valid time, it checks if the system 
        clock is in sync with the RTC. If not, it synchronizes the system 
        clock to the RTC time. This ensures that all timestamps in the data 
        logging are accurate and consistent, even if the Raspberry Pi loses 
        power or experiences a reset during the mission.
        
        Raises:
            Exception: If there is an error reading from the RTC or synchronizing 
            the system clock, an error message is printed, but the mission continues.
        """
        self.curr_time = time.time()
        try:
            if self.rtc:
                if self.rtc.connected:
                    if self.rtc.read_data() != self.curr_time:
                        self.rtc.sync_system_clock()
                        self.curr_time = time.time()
        except Exception as e:
            print(e)

    def handle_data_collection(self):
        """
        Handles data collection from all sensors. It reads data from each 
        sensor, checks for validity (e.g., NaN values), and packs the data 
        into a CCSDS-compliant binary format for logging. If any sensor 
        fails to provide valid data, it sets the corresponding status flag 
        to 0. This method is called at the defined sample rate to ensure 
        consistent data collection throughout the mission.
        
        Raises:
            Exception: If there is an error reading from any sensor, an error 
            message is printed, but the mission continues with the available data.
        """

        # Define NaN values for failed sensor reads
        nan = float("nan")
        triple_nan = (nan, nan, nan)
        quad_nan = (nan, nan, nan, nan)

        # Reset loop time to current time
        self.loop_start = self.curr_time

        def is_failed(data):
            """
            Helper function to check if sensor data is valid. 
            It checks for NaN values in the data, which 
            indicate a failed sensor read.
            
            Args:
                data (list or tuple): The sensor data to check, 
                which can be a single value or a list
            """
            # Accept list/tuple (and any nested tuples)
            if isinstance(data, (list, tuple)):
                for x in data:
                    if isinstance(x, (list, tuple)):
                        if is_failed(x):
                            return True
                    else:
                        if isinstance(x, float) and math.isnan(x):
                            return True
                return False

            # Single scalar
            return isinstance(data, float) and math.isnan(data)

        # --- RTC STATUS ---
        if self.rtc:
            try:
                t = self.rtc.read_data()
                # print(f"RTC read time: {t}")
                if is_failed(t):
                    rtc_status = 0
                else:
                    rtc_status = 1
            except Exception as e:
                t = nan
                imu_status = 0
                print(f"RTC read error: {e}")

        else:
            t = nan
            rtc_status = 0

        # --- IMU ---
        if self.imu:
            try:
                accel, gyro, mag = self.imu.get_data()
                # print(f"IMU read accel: {accel}, gyro: {gyro}, mag: {mag}")
                # If any part of the IMU read is NaN, mark as FAIL
                if is_failed(accel) or is_failed(gyro) or is_failed(mag):
                    imu_status = 0
                else:
                    imu_status = 1
            except Exception as e:
                accel, gyro, mag = triple_nan, triple_nan, triple_nan
                imu_status = 0
                print(f"IMU read error: {e}")

        else:
            accel, gyro, mag = triple_nan, triple_nan, triple_nan
            imu_status = 0

        # --- TEMPERATURE SENSORS ---
        if self.temp:
            try:
                t_data = self.temp.get_all_temps()
                # print(f"Temp sensor read: {t_data}")
                temp_status = 0 if is_failed(t_data) else 1
            except Exception as e:
                t_data = quad_nan
                temp_status = 0
                print(f"Temp sensor read error: {e}")
        else:
            t_data = quad_nan
            temp_status = 0

        # --- BME280 ---
        if self.bme280:
            try:
                bme_data = self.bme280.get_data()
                # print(f"BME280 read: {bme_data}")
                bme280_status = 0 if is_failed(bme_data) else 1
            except Exception as e:
                bme_data = triple_nan
                bme280_status = 0
                print(f"BME 280 read error: {e}")
        else:
            bme_data = triple_nan
            bme280_status = 0

        # --- INA219 ---
        if self.ina219:
            try:
                ina_data = self.ina219.read_data()
                # print(f"INA219 read: {ina_data}")
                ina219_status = 0 if is_failed(ina_data) else 1
            except Exception as e:
                ina_data = triple_nan
                ina219_status = 0
                print(f"INA 219 read error: {e}")
        else:
            ina_data = triple_nan
            ina219_status = 0

        # --- MPL3115A2 ---
        if self.mpl:
            try:
                mpl_data = self.mpl.read_data()
                # print(f"MPL3115A2 read: {mpl_data}")
                mpl_status = 0 if is_failed(mpl_data) else 1
            except Exception as e:
                mpl_data = nan
                mpl_status = 0
                print(f"MPL read error: {e}")
        else:
            mpl_data = nan
            mpl_status = 0

        # --- GPS ---
        if self.gps:
            try:
                gps_data = self.gps.read_data()
                lat, lon, alt = gps_data
                if any(
                    not math.isnan(val) for val in [lat, lon, alt]
                ):  # Check if any value is valid
                    gps_status = 1
                else:
                    gps_data = triple_nan
                    gps_status = 0
                # print(f"GPS read: {gps_data}")
            except Exception as e:
                gps_data = triple_nan
                gps_status = 0
                print(f"GPS read error: {e}")
        else:
            gps_data = triple_nan
            gps_status = 0

        # Pack for CCSDS (Converts to binary fomat for efficient logging)
        # I = unsigned int (4 bytes), f = float (4 bytes), B = unsigned char (1 byte)
        # print(f"Packing data for CCSDS logging: Time={t}, Temps={t_data}, Accel={accel}, Gyro={gyro}, Mag={mag}, BME={bme_data}, INA={ina_data}, MPL={mpl_data}, GPS={gps_data}, Statuses: RTC={rtc_status}, IMU={imu_status}, Temp={temp_status}, BME280={bme280_status}, INA219={ina219_status}, MPL={mpl_status}, GPS={gps_status}")
        payload = struct.pack(
            ">Iffff fff fff fff fff fff f fff BBBBBBB",
            int(self.curr_time),
            *t_data,
            *accel,
            *gyro,
            *mag,
            *bme_data,
            *ina_data,
            mpl_data,
            *gps_data,
            bme280_status,
            ina219_status,
            imu_status,
            temp_status,
            mpl_status,
            gps_status,
            rtc_status,
        )

        # Log the data in data folder with CCSDS format (Binary)
        # print(f"Logging data to CCSDS: {len(payload)} bytes")
        self.logger.write(payload)

        # print(f"Data collection complete. RTC Status: {rtc_status} | IMU Status: {imu_status} | Temp Status: {temp_status} | BME280 Status: {bme280_status} | INA219 Status: {ina219_status} | MPL Status: {mpl_status} | GPS Status: {gps_status}")
        self.bme280_status = bme280_status
        self.ina219_status = ina219_status
        self.imu_status = imu_status
        self.temp_status = temp_status
        self.mpl_status = mpl_status
        self.gps_status = gps_status
        self.rtc_status = rtc_status

    def handle_reinitialization(self):
        """
        Handles sensor re-initialization if any sensor has failed. 
        If the current time exceeds the last re-initialization time 
        by the defined reinitialization duration, it attempts to 
        re-initialize all sensors. This allows the mission to recover 
        from temporary sensor failures and continue collecting data 
        with whatever sensors are available.
        """
        if self.curr_time - self.last_reinit >= self.reinit_dur:
            print("\nAttempting sensor reinitialization...")
            self.initialize_sensors()
            self.last_reinit = self.curr_time

    def handle_photos(self):
        """
        Handles photo capture if the camera is connected and in photo mode.
        It checks if the current time exceeds the last photo capture time
        
        Raises:
            Exception: If there is an error capturing a photo, an error 
            message is printed, but the mission continues.
        """
        # Capture at defined camera rate
        if self.curr_time - self.last_photo_time >= (
            1.0 / self.photo_rate
        ):  
            try:
                # Take pictures at every interval
                self.camera.take_picture(f"frame_{int(time.time())}.jpg")
            except Exception as e:
                print(f"Error capturing camera frame: {e}")
            self.last_photo_time = time.time()

    def handle_video_recording(self):
        """
        Handles video recording if the camera is connected and in video mode.
        If not currently recording, it starts a new video. If currently recording,
        it checks if the recording duration has been exceeded and stops the video if so.
        
        Raises:
            Exception: If there is an error starting or stopping video recording, 
            an error message is printed, but the mission continues."""
        if not self.video_active:
            try:
                self.camera.start_video(f"video_{int(time.time())}.h264")
                self.video_active = True
                self.last_video_time = time.time()
            except Exception as e:
                print(f"Failed to start video: {e}")
        else:
            if self.curr_time - self.last_video_time >= self.video_duration:
                try:
                    self.camera.stop_video()
                    self.video_active = False
                except Exception as e:
                    print(f"Failed to stop video: {e}")

    def handle_led_toggle(self):
        """
        Handles LED toggling for visual status indication. If the LED is connected, 
        it toggles the LED state at defined intervals to provide a visual heartbeat 
        of the mission's operation. This can be useful for quick visual checks of the 
        system status during flight.
        
        Raises:
            Exception: If there is an error toggling the LED, an error message is printed, 
            but the mission continues.
        """
        if self.led:
            try:
                if self.curr_time - self.last_led_flash >= self.led_flash_dur:
                    self.led.toggle()
                    self.last_led_flash = self.curr_time
            except Exception as e:
                print(f"Error toggling LED: {e}")

    def run(self):
        """
        The main mission loop.
        
        Raises:
            KeyboardInterrupt: If a shutdown signal is received, the loop will exit
            and perform cleanup.
            Exception: If any unexpected error occurs during the mission, an error
            message is printed, but the program will attempt to continue running."""
        print(f"Mission Started. Rate: {self.sample_rate}Hz")

        try:
            while True:
                # self.curr_time = time.time()
                self.handle_time_sync()

                # Define loop time to ensure measurement at specified Hz
                elapsed = self.curr_time - self.loop_start
                wait_time = (1.0 / self.sample_rate) - elapsed
                if wait_time > 0:
                    # print(f"Waiting {wait_time:.2f}s to maintain sample rate...")
                    time.sleep(0.01)

                # Gather data at specified Hz
                else:
                    self.handle_led_toggle()
                    self.handle_data_collection()
                    # print(f"Collecting data at {self.curr_time:.2f} (Elapsed: {elapsed:.2f}s)")
                    self.handle_reinitialization()

                    # Camera Logic (pass if not connecyed)
                    if self.camera:
                        if self.camera_connected:
                            if self.camera_mode == "still":
                                self.handle_photos()
                            else:
                                self.handle_video_recording()

                    time.sleep(
                        0.01
                    )  # Short sleep to prevent CPU hogging; adjust as needed
                    # break  # Uncomment this to only test one loop iteration; it's here just for testing purposes.

        # Handle graceful exit
        except KeyboardInterrupt:
            print("Ending script")
        finally:
            print("\nCleaning up GPIO...")
            try:
                if self.camera:
                    self.camera.cleanup()
            except:
                pass
            try:
                if self.led:
                    self.led.off()
                    self.led.cleanup()
            except:
                pass
            import RPi.GPIO as GPIO

            GPIO.cleanup()


if __name__ == "__main__":
    # tells watchdog script to run cleanup
    signal.signal(signal.SIGTERM, service_shutdown)
    signal.signal(signal.SIGINT, service_shutdown)

    # Pass that result into your class
    mission = FlightStateMachine(sample_rate=10)
    mission.run()
