import qwiic_bme280
import time
import sys

def runExample():

	print("\nSparkFun BME280 Sensor  Example 1\n")
	mySensor = qwiic_bme280.QwiicBme280()

	if mySensor.connected == False:
		print("The Qwiic BME280 device isn't connected to the system. Please check your connection", \
			file=sys.stderr)
		return

	mySensor.begin()

	while True:
		print("Humidity:\t%.3f" % mySensor.humidity)

		print("Pressure:\t%.3f" % mySensor.pressure)	

		print("Altitude:\t%.3f" % mySensor.altitude_feet)

		print("Temperature:\t%.2f" % mySensor.temperature_fahrenheit)		

		print("")
		
		time.sleep(1)