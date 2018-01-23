import RPi.GPIO as GPIO
import time
import sys

class valve:
	def __init__(self): #add nice parameters for pin numbers
		self.atm = 23
		self.tores = 29
		self.tocyl = 31
		self.ids = [self.atm,self.tores,self.tocyl]
		GPIO.setmode(GPIO.BOARD)
		GPIO.setup(self.ids, GPIO.OUT)

	def activate(self,id,sec): #do this without sleeping
		try:
			if id == "atm":
				GPIO.output(self.atm,GPIO.HIGH)
				time.sleep(sec)
				GPIO.output(self.atm,GPIO.LOW)
			elif id == "tores":
				GPIO.output(self.tores,GPIO.HIGH)
				time.sleep(sec)
				GPIO.output(self.tores,GPIO.LOW)
			elif id == "tocyl":
				GPIO.output(self.tocyl,GPIO.HIGH)
				time.sleep(sec)
				GPIO.output(self.tocyl,GPIO.LOW)
			else:
				print("incorrect valve id")
		except:
			print("Unexpected error:", sys.exc_info()[0])
			GPIO.cleanup()
			raise
