import RPi.GPIO as GPIO
import time
import sys


class Valve:
	def __init__(self): #add nice parameters for pin numbers
		self.atm = 40
		self.tores = 36
		self.tocyl = 38
		self.ids = [self.atm,self.tores,self.tocyl]
		GPIO.setmode(GPIO.BOARD)
		GPIO.setup(self.ids, GPIO.OUT)

	def activate(self, ids, sec): #do this without sleeping
		try:
			if ids == "atm":
				GPIO.output(self.atm, GPIO.HIGH)
				time.sleep(sec)
				GPIO.output(self.atm, GPIO.LOW)
			elif ids == "tores":
				GPIO.output(self.tores, GPIO.HIGH)
				time.sleep(sec)
				GPIO.output(self.tores, GPIO.LOW)
			elif ids == "tocyl":
				GPIO.output(self.tocyl, GPIO.HIGH)
				time.sleep(sec)
				GPIO.output(self.tocyl, GPIO.LOW)
			else:
				print("incorrect valve id")
		except:
			print("Unexpected error:", sys.exc_info()[0])
			GPIO.cleanup()
			raise


if __name__ == "__main__":
	GPIO.cleanup()
	v = Valve()
	v.activate("tocyl", 2)
	print("1")
	time.sleep(2)
	v.activate("tocyl", 2)
	print("2")
	time.sleep(2)
	v.activate("tocyl", 2)
	print("3")
	time.sleep(2)
	v.activate("tocyl", 2)
	print("4")
	time.sleep(2)