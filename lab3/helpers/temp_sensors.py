import ADS1x15
import RPi.GPIO as GPIO
import math
class TempSensor:
    """
    PURPOSE: Handles ADS1115 ADC conversion and Steinhart-Hart thermistor math.
    REASONING: Complex math should be hidden inside the class to prevent clutter.
    """
    def __init__(self, gpio_pin=15):
        self.ads1 = ADS1x15.ADS1115(1, 0x49)
        self.ads2 = ADS1x15.ADS1115(1, 0x48)
        self.gpio_pin = gpio_pin
        
        # Steinhart-Hart Coefficients
        self.A, self.B, self.C, self.D = 1.0219e-3, 2.4145e-4, -2.4762e-7, 1.6539e-7
        self.R_VAL, self.VCC = 6800, 3.3

        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.gpio_pin, GPIO.OUT)

    def _calc_temp(self, res):
        """Converts resistance to Celsius."""
        if res <= 0:
            print(f"Warning: Invalid resistance reading: {res}")
            return 0.0  # Return a dummy value to prevent crash
        ln_r = math.log(res)
        inv_t = self.A + (self.B * ln_r) + (self.C * ln_r**2) + (self.D * ln_r**3)
        return 1/inv_t - 273.15

    def get_all_temps(self):
        """Reads ADCs and returns a list of 5 temperatures."""
        f1, f2 = self.ads1.toVoltage(), self.ads2.toVoltage()
        
        # Read raw ADC and convert to Voltage -> Resistance -> Temp
        raw_vals = [self.ads1.readADC(0), self.ads1.readADC(1), 
                    self.ads1.readADC(2), self.ads1.readADC(3), self.ads2.readADC(1)]
        
        temps = []
        for i, val in enumerate(raw_vals):
            v = val * (f1 if i < 4 else f2)
            
            # Check if voltage is too low to be a real reading
            if v <= 0.001: 
                print(f"Warning: Sensor {i} reading 0V! Check wiring.")
                r = 0 
            else:
                r = ((self.R_VAL * self.VCC) / v) - self.R_VAL
            
            temps.append(self._calc_temp(r))
        return temps

    def set_led_alert(self, state):
        """Toggles the GPIO pin based on threshold logic."""
        GPIO.output(self.gpio_pin, GPIO.HIGH if state else GPIO.LOW)