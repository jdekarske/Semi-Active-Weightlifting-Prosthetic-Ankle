#!/usr/bin/env python
import time
import RPi.GPIO as GPIO
import threading
import csv
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
		self.kp = .0000001
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
						print("pump it! Louder! Pump it! Louder! alright alright alright alright")
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
		self.ledr = 11
		self.ledg = 13
		self.ledb = 15
		self.leds = [self.ledr, self.ledg, self.ledb]
		GPIO.setup(self.leds, GPIO.OUT, initial=GPIO.LOW)
		#  input from menu first arguement is a new update
		#  "startup", "error", "low pressure", "connecting/disconnected(white)",
		#  "calibrate/calibrating(blue)", "walking/lifting(green)" in order of priority
		self.systemstatus = [False, [True, False, False, False, False, True]]
		#  menu items are those with slashes
		self.menu = 1
		self.activecolor = self.ledr
		self.fast = fastspeed
		self.slow = slowspeed
		self.const = 69  # if this speed stay on
		self.speed = self.const
		self.lasttime = time.time()
		self.on = False

	def __checkled(self):
		if self.systemstatus[0]:  # flag the leds to change state
			self.systemstatus[0] = False
			if self.systemstatus[1][0]:  # startup
				self.activecolor = self.ledr
				self.speed = self.slow
			elif self.systemstatus[1][1]:  # error
				self.activecolor = self.ledr
				self.speed = self.const
			elif self.systemstatus[1][2]:  # low pressure
				self.activecolor = self.ledr
				self.speed = self.fast
			else:
				if self.menu == 0:  # bluetooth stuff
					if self.systemstatus[1][3]:  # disconnected
						self.activecolor = self.leds
						self.speed = self.slow
					else:  # connecting
						self.activecolor = self.leds
						self.speed = self.fast
				elif self.menu == 1:  # calibration stuff
					if self.systemstatus[1][4]:  # calibrating
						self.activecolor = self.ledb
						self.speed = self.slow
					else:  # calibrate
						self.activecolor = self.ledb
						self.speed = self.fast
				elif self.menu == 2:
					if self.systemstatus[1][5]:  # walking
						self.activecolor = self.ledg
						self.speed = self.slow
					else:  # "lifting"
						self.activecolor = self.ledg
						self.speed = self.fast

	def __flash(self):  # can probably implement this in hardware
		if self.speed == self.const:  # stay on
			GPIO.output(self.leds, GPIO.LOW)   # clear all leds
			GPIO.output(self.activecolor, GPIO.HIGH)  # then turn on the desired one
		else:
			now = time.time()
			if now > (self.lasttime + self.speed):
				self.lasttime = now
				GPIO.output(self.leds, GPIO.LOW)
				if self.on:
					self.on = False
					GPIO.output(self.activecolor, GPIO.HIGH)
				else:
					self.on = True  # the led is off anyway, but turn it on next loop

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
				self.__flash()
		finally:
			print("clean LED exit!")
			GPIO.cleanup()

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