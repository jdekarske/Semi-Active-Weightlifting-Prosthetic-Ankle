#!/usr/bin/env python
import time
import RPi.GPIO as GPIO
import threading
import csv
import PCA9553
GPIO.setmode(GPIO.BOARD)
GPIO.setwarnings(False)


class Valves(threading.Thread):
	def __init__(self, getpressure_function):
		threading.Thread.__init__(self)
		self._stop_event = threading.Event()
		self.getbluetoothmsg = None
		self.atm = 40
		self.tores = 36
		self.tocyl = 38
		self.getpressure = getpressure_function
		self.valves = [self.atm, self.tores, self.tocyl]
		self.commandpressure = 20
		GPIO.setup(self.valves, GPIO.OUT, initial=GPIO.LOW)
		self.threshold = 2
		self.kp = .000001
		self.kpatm = .01

		self.defaultwalk = 20
		self.defaultsquat = 20
		self.defaultdeadlift = 20
		self.defaultpress = 20

	def setpressure(self, receivedpressure):
		with open('pressurechange.csv', 'a') as csvfile:
			looptimeout = time.clock()
			spamwriter = csv.writer(csvfile)
			self.commandpressure = receivedpressure
			[cpressure, rpressure] = self.getpressure()
			mode = 0
			while (abs(self.commandpressure - cpressure) > self.threshold) and (time.clock()-looptimeout < 5):
				cerror = self.commandpressure - cpressure
				rerror = rpressure - cpressure
				dur = abs(cerror*self.kp)
				duratm = dur**(.33)
				if cerror > 0:
					if rerror > 0:
						self.activate("tocyl", dur)
						print("tocyl")
						print(dur)
						mode = 10
					else:
						print("Look, pump it up if you came to get it crunk")
						mode = 20
						break
				elif rerror > -1:
					self.activate("atm", duratm)
					print("atm")
					print(duratm)
					mode = 30
				else:
					self.activate("tores", dur)
					print("tores")
					print(dur)
					mode = 40
				time.sleep(.1)  #give the valves a little break and sample more

				spamwriter.writerow([mode, receivedpressure, cpressure, rpressure, dur, duratm])
				csvfile.flush()
				[cpressure, rpressure] = self.getpressure()

	def activate(self, valve, sec):
		# try:
		if sec < .000003:  # fastest it can go at 40psi
			sec = .000003
		elif sec > 10:
			sec = 10
		if valve == "atm":
			v = self.atm
		elif valve == "tores":
			v = self.tores
		elif valve == "tocyl":
			v = self.tocyl
		GPIO.output(v, GPIO.HIGH)
		time.sleep(sec)
		GPIO.output(v, GPIO.LOW)
		# except:
		# 	print(e)
		# 	GPIO.cleanup()
		# 	raise

	def setbluetoothfunction(self, bluetoothfunction):
		self.getbluetoothmsg = bluetoothfunction

	def run(self):
		while not self._stop_event.is_set():
			try:
				[flag, command] = self.getbluetoothmsg()
				print(flag)
				print(command)
				if flag == "s":  # settings
					self.defaultwalk = int(command[0])
					self.defaultsquat = int(command[1])
					self.defaultdeadlift = int(command[2])
					self.defaultpress = int(command[3])
					flag = None
				elif flag == "c":  # direct command
					if command == 0:
						self.activate("tores", 9)
					else:
						self.setpressure(command)
						flag = None
				elif flag == "m":  # change mode
					if command == "w":
						self.setpressure(self.defaultwalk)
					elif command == "s":
						self.setpressure(self.defaultsquat)
					elif command == "d":
						self.setpressure(self.defaultdeadlift)
					elif command == "p":
						self.setpressure(self.defaultpress)
					flag = None
			except TypeError, e:
				pass
				# print(e)

	def set_stop_event(self):  # sets a flag to kill this Thread.
		self._stop_event.set()


class LED(threading.Thread):
	def __init__(self, fastspeed=.1, slowspeed=1):
		threading.Thread.__init__(self)
		self._stop_event = threading.Event()
		#  input from menu first arguement is a new update
		#  "startup", "error", "low pressure", "connecting/disconnected(white)",
		#  "calibrate/calibrating(blue)", "walking/lifting(green)" in order of priority
		self.systemstatus = [False, [True, False, False, False, False, True]]
		#  menu items are those with slashes
		self.menu = 1
		self.fast = fastspeed
		self.slow = slowspeed
		pca = PCA9553()
		pca.setBlink(0,self.slow) # time between blinks
        pca.setBlink(1,self.fast)

	def __checkled(self):
		if self.systemstatus[0]:  # flag the leds to change state
			self.systemstatus[0] = False
			if self.systemstatus[1][0]:  # startup
				self.pca.setLED(PCA9553.CHRED,2)
			elif self.systemstatus[1][1]:  # error
				self.pca.setLED(PCA9553.CHRED,0)
			elif self.systemstatus[1][2]:  # low pressure
				self.pca.setLED(PCA9553.CHRED,3)
			else:
				if self.menu == 0:  # bluetooth stuff
					if self.systemstatus[1][3]:  # disconnected
						self.pca.setLED(PCA9553.CHRED,2)
						self.pca.setLED(PCA9553.CHBLUE,2)
						self.pca.setLED(PCA9553.CHGREEN,2)
					else:  # connecting
						self.pca.setLED(PCA9553.CHRED,3)
						self.pca.setLED(PCA9553.CHBLUE,3)
						self.pca.setLED(PCA9553.CHGREEN,3)
				elif self.menu == 1:  # calibration stuff
					if self.systemstatus[1][4]:  # calibrating
						self.pca.setLED(PCA9553.CHBLUE,2)
					else:  # calibrate
						self.pca.setLED(PCA9553.CHBLUE,3)
				elif self.menu == 2:
					if self.systemstatus[1][5]:  # walking
						self.pca.setLED(PCA9553.CHGREEN,2)
					else:  # "lifting"
						self.pca.setLED(PCA9553.CHGREEN,3)

	def get_status(self):
		return self.systemstatus[1]

	def set_status(self, status, switch):
		if status == "startup":
			self.systemstatus[1][0] = switch
		elif status == "error":
			self.systemstatus[1][1] = switch
		elif status == "low pressure":
			self.systemstatus[1][2] = switch
		elif status == "connecting":
			self.systemstatus[1][3] = switch
		elif status == "calibrating":
			self.systemstatus[1][4] = switch
		elif status == "walking":
			self.systemstatus[1][5] = switch
		else:
			print("incorrect id")
		self.systemstatus[0] = True

	def set_menu(self, menu):
		self.menu = menu
		self.systemstatus[0] = True

	def run(self):
		try:
			while not self._stop_event.is_set():
				self.__checkled()
		finally:
			print("clean LED exit!")

	def set_stop_event(self):  # sets a flag to kill this Thread.
		self._stop_event.set()


if __name__ == "__main__":  # test
	import Utils
	v = Valves(getpressure_function=None)
	p = Utils.Sensors()
	ii = 0
	with open('pressures.csv', 'a') as csvfile:
		looptimeout = time.clock()
		spamwriter = csv.writer(csvfile)
		v.activate('tores', 10)
		time.sleep(1)
		v.activate('atm', 5)
		while True:
			ii += .001
			p.readsensors()
			first = p.get_pressures()
			v.activate('tocyl', ii)
			p.readsensors()
			second = p.get_pressures()
			print(ii)
			print(first)
			if abs(second[0]-second[1]) < 4:
				v.activate("atm", 5)
			if second[1] < 24:
				break
			spamwriter.writerow([ii, first[0], first[1], second[0], second[1]])
			csvfile.flush()
			time.sleep(1)







	# lights = LED()
	# lights.setDaemon(True)
	# lights.start()
	# lights.set_status("startup", True)
	# print("startup")
	# time.sleep(15)
	# lights.set_status("startup", False)
	# lights.set_status("error", True)
	# print("error")
	# time.sleep(15)
	# lights.set_status("error", False)
	# lights.set_status("low pressure", True)
	# print("low pressure")
	# time.sleep(15)
	# lights.set_status("low pressure", False)
	# for fmenu in [0, 1, 2]:
	# 	print(fmenu)
	# 	lights.set_menu(fmenu)  # "f"status because PEP gives a shadow error and I don't like squigly lines
	# 	lights.set_status("connecting", True)
	# 	lights.set_status("calibrating", True)
	# 	lights.set_status("walking", True)
	# 	time.sleep(5)
	# 	lights.set_status("connecting", False)
	# 	lights.set_status("calibrating", False)
	# 	lights.set_status("walking", False)
	# 	time.sleep(5)
	# lights.set_stop_event()