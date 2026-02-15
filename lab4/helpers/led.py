import time
import lgpio

class LEDIndicator:
    """
    PURPOSE: Handles GPIO control for a status LED on Pin 26.
    ERROR HANDLING: If the GPIO chip fails to open, the class marks itself as 
    not connected. Methods will skip execution rather than crashing the main loop.
    """

    def __init__(self, pin=26):
        self.pin = pin
        self.state = 0  # 0 = Off, 1 = On
        
        try:
            # Open the GPIO chip (usually 0 on Raspberry Pi)
            self.chip = lgpio.gpiochip_open(0)
            # Set the pin as an output
            lgpio.gpio_claim_output(self.chip, self.pin)
            self.connected = True
            print(f"[LED Initialized]: GPIO {pin} ready.")
        except Exception as e:
            print(f"[LED Initialization Error]: Could not claim GPIO {pin}: {e}")
            self.connected = False

    def on(self):
        """Turns the LED on (High)."""
        if not self.connected:
            return
        try:
            lgpio.gpio_write(self.chip, self.pin, 1)
            self.state = 1
        except Exception as e:
            print(f"[LED Error]: Failed to write HIGH: {e}")

    def off(self):
        """Turns the LED off (Low)."""
        if not self.connected:
            return
        try:
            lgpio.gpio_write(self.chip, self.pin, 0)
            self.state = 0
        except Exception as e:
            print(f"[LED Error]: Failed to write LOW: {e}")

    def toggle(self):
        """Flips the current state of the LED."""
        if self.state == 0:
            self.on()
        else:
            self.off()

    def cleanup(self):
        """Releases the GPIO chip."""
        if self.connected:
            lgpio.gpiochip_close(self.chip)