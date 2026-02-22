"""
-------------------------------------------------------------------------------
Project: Thermistor Temperature Sensor Class for High-Altitude Balloon Mission

File:    temp_sensors.py

Purpose: Handles reading and processing temperature data from thermistor sensors.
         Uses ADS1115 ADC and Steinhart-Hart equation for temperature conversion.
         Provides a clean interface for reading multiple thermistor temperatures.

Logic:   1. Initializes the ADS1115 ADC and sets up GPIO for sensor status 
            indication.
         2. Reads raw ADC values from 4 thermistor channels.
         3. Converts raw ADC values to voltages, then to resistance, and 
            finally to temperature in Celsius.
         4. Handles sensor disconnection or invalid readings by returning 
            NaN values and printing warnings.

If run as main:
         1. Initializes the TempSensor class.
         2. Continuously reads and prints the temperatures from all 4 sensors every second.
         3. Handles keyboard interrupt to exit gracefully.
-------------------------------------------------------------------------------
Author:  Kenadi Waymire
Date:    February 2026
-------------------------------------------------------------------------------
"""

import ADS1x15
import RPi.GPIO as GPIO
import math
class TempSensor:
    """
    PURPOSE: Handles ADS1115 ADC conversion and Steinhart-Hart thermistor math.
    REASONING: Complex math should be hidden inside the class to prevent clutter.
    """
    def __init__(self, gpio_pin=15):
        try:
            self.ads1 = ADS1x15.ADS1115(1, 0x48)
            self.gpio_pin = gpio_pin
            self.ads1.setGain(1)
            
            # Steinhart-Hart Coefficients
            self.A, self.B, self.C, self.D = 1.0219e-3, 2.4145e-4, -2.4762e-7, 1.6539e-7
            self.R_VAL, self.VCC = 51000, 3.3

            GPIO.setmode(GPIO.BCM)
            GPIO.setup(self.gpio_pin, GPIO.OUT)
            self.connected = True
        except Exception as e:
            print(f"[TempSensor Initialization Error]: {e}")
            self.connected = False

    def _calc_temp(self, res):
        """Converts resistance to Celsius."""

        if res <= 0 or res is None or res == float('nan'):
            print(f"Warning: Invalid resistance reading: {res}")
            return float('nan')  # Return a NaN value to prevent crash
        
        ln_r = math.log(res)
        inv_t = self.A + (self.B * ln_r) + (self.C * ln_r**2) + (self.D * ln_r**3)
        return 1/inv_t - 273.15

    def get_all_temps(self):
        """Reads ADCs and returns a list of 4 temperatures."""
        
        # return nan if sensors all disconnected
        nan = float('nan')
        if not self.connected:
            return [nan] * 4
        try:
            f1 = self.ads1.toVoltage()
            
            # Read raw ADC and convert to Voltage -> Resistance -> Temp
            raw_vals = [self.ads1.readADC(0), self.ads1.readADC(1), 
                        self.ads1.readADC(2), self.ads1.readADC(3)]
            # print(f"Raw ADC values: {raw_vals}")
            
            # for each sensor, check if voltage is too low to be a real reading; 
            # if so, print warning and return NaN for that sensor. 
            # Otherwise, calculate resistance and temp as normal.
            temps = []
            for i, val in enumerate(raw_vals):
                # Convert raw ADC to voltage (using f1 for first 4 sensors, f2 for last sensor)
                v = val * f1
                
                # Check if voltage is too low to be a real reading
                if v <= 0.001: 
                    print(f"Warning: Sensor {i} reading <0.001V! Check wiring.")
                    temps.append(nan)
                    continue
                    r = 0 
                else:
                    r = ((self.R_VAL * self.VCC) / v) - self.R_VAL
                    try:
                        temp = self._calc_temp(r)
                    except Exception as e:
                        print(f"[TempSensor Math Error]: {e}")
                        temp = nan
                    temps.append(temp)

            return temps
        except Exception as e:
            print(f"[TempSensor Data Error]: {e}")
            return [nan] * 4

    # def set_led_alert(self, state):
    #     """Toggles the GPIO pin based on threshold logic."""
    #     GPIO.output(self.gpio_pin, GPIO.HIGH if state else GPIO.LOW)
