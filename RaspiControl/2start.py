# file: rfcomm-server.py
# auth: Albert Huang <albert@csail.mit.edu>
# desc: simple demonstration of a server application that uses RFCOMM sockets
#
# $Id: rfcomm-server.py 518 2007-08-10 07:20:07Z albert $
import numpy as np
from bluetooth import *
from readADC import readADC
import time
import sys
import RPi.GPIO as GPIO
import threading
import valvecontrol as v
import jlogging as j
GPIO.setwarnings(False)

class outputs:
        def __init__(self): #add nice parameters for pin numbers
                #valves
                self.atm = 23
                self.tores = 29
                self.tocyl = 31
                self.valves = [self.atm,self.tores,self.tocyl]
                #leds
                self.button   = 36
                self.ledr = 33
                self.ledg = 37
                self.ledb = 35
                self.leds = [self.ledr,self.ledg,self.ledb]
                GPIO.setmode(GPIO.BOARD)
                GPIO.setup(self.button, GPIO.IN, pull_up_down=GPIO.PUD_UP)
                GPIO.setup(self.valves, GPIO.OUT, initial=GPIO.LOW)
                GPIO.setup(self.leds, GPIO.OUT, initial=GPIO.LOW)
		#control
		self.meanp0 = 50 #THIS IS AN ISSUE
		self.psi = 80
		self.kp = .002 #we can model this extremely accurately, this is a project for january
		self.rate = .02
		self.threshold = 10
		self.go = False
	def wait4button(self):
		GPIO.wait_for_edge(self.button, GPIO.RISING)
		j.debug("button press")

        def activate(self,item,sec): #do this without sleeping, this probably sucks anyway
                try:
                        if sec < .001:
                                sec = .001
                        elif sec > 15:
                                sec = 15
                        elif item == "atm":
                                v = self.atm
                        elif item == "tores":
                                v = self.tores
                        elif item == "tocyl":
                                v = self.tocyl
                        elif item == "red":
                                v = self.ledr
                        elif item == "green":
                                v = self.ledg
                        elif item == "blue":
                                v = self.ledb
                        else:
                                j.error("incorrect item")
                        GPIO.output(v,GPIO.HIGH)
                        time.sleep(sec)
                        GPIO.output(v,GPIO.LOW)

                except:
                        j.error("Unexpected GPIO error:" + str(sys.exc_info()[0]))
                        GPIO.cleanup()
                        raise
        def led(self,color,on):
                try:
                        if color == "red":
                                v = self.ledr
                        elif color == "green":
                                v = self.ledg
                        elif color == "blue":
                                v = self.ledb
                        else:
                                j.error("incorrect color id")
                        if on:
                                GPIO.output(v,GPIO.HIGH)
                        elif on == 0:
                                GPIO.output(v,GPIO.LOW)
                        elif on == 3: #indicates processing, probably a poor way to do so
                                GPIO.output(v,GPIO.HIGH)
                                time.sleep(.01)
                                GPIO.output(v,GPIO.LOW)
                        else:
                                j.error("incorrect led command")
                except:
                        j.error("Unexpected GPIO error:" + sys.exc_info()[0])
                        GPIO.cleanup()
                        raise

        def flashLed(self,e, t, color):
            #flash the specified led every half second
		if color == "red":
			self.c = self.ledr
		elif color == "green":
			self.c = self.ledg
		elif color == "blue":
			self.c = self.ledb
		else:
			j.error("invalid flashled color")
			raise
		while not e.isSet():
                	GPIO.output(self.c,GPIO.HIGH)
                	time.sleep(t)
                	event_is_set = e.is_set()
                	if event_is_set:
				break
                	else:
                	    	GPIO.output(self.c,GPIO.LOW)
                	    	time.sleep(t)
	def streaming(self,e):
		#for smoothing need to add a function
		max_samples = 10
		p0 = []
		p1 = []
		p2 = []
		p3 = []

		while not e.isSet():
			try:
				read = readADC()
		        	p0 = np.append(p0,read[0]) #make this better
                		p1 = np.append(p1,read[1])
                		#p2 = np.append(p2,read[2]) #don't need these for now
                		#p3 = np.append(p3,read[3])
                		self.meanp0 = np.mean(p0)
                		self.meanp1 = np.mean(p1)
                		#meanp2 = np.mean(p2)
                		#meanp3 = np.mean(p3)
                		client_sock.send(str(round(self.meanp0,1))+'/'+str(round(self.meanp1,1))) #+'/'+str(round(meanp2,1))+'/'+str(round(meanp3,1))
	                	if len(p0) == max_samples:
	                	        p0 = np.delete(p0, 0)
	                	        p1 = np.delete(p1, 0)
	                	        #p2 = np.delete(p2, 0)
	                	        #p3 = np.delete(p3, 0)
				event_is_set = e.is_set()
				time.sleep(.01)
				#if event_is_set: redundant?
				#	break
                        	#else:
                        	#        time.sleep(.01)
			except:
		        	print("stream error: "  + str(IOError))
				pass
	def setpsi(self):
		while True:
			while (abs(self.psi-self.meanp0) > self.threshold)  & self.go:
				error = self.psi-self.meanp0
				dur = abs(self.kp*error)
				print("-------")
				print(self.psi)
				print(self.meanp0)
				print(self.meanp1)
				print(error)
				print(dur)
				if error > 0:
					self.activate("tocyl",dur)
					print("tocyl")
				elif error < 0:
					if self.meanp1 < (self.meanp0-15): #if the resovoir is more pressurized let air out of the system
						self.activate("tores",dur)
						print("tores")
					else:
						ndur = dur/2
						self.activate("atm",(ndur))
						print("atm")
				time.sleep(self.rate)
			self.go = False

a=outputs()

re = threading.Event()
rt = threading.Thread(name='redslow', target=a.flashLed, args=(re,1,"red"))
rt.daemon = True
rt.start()

a.activate("tores",10)
a.wait4button()
re.set() #stop flashing
re2 = threading.Event() #FLASH FASTER YEEAAHH
rt2 = threading.Thread(name='redfast', target=a.flashLed, args=(re2,.1,"red"))
rt2.daemon = True
rt2.start()

#bluetooth setup
server_sock=BluetoothSocket( RFCOMM )
server_sock.bind(("",PORT_ANY))
server_sock.listen(1)
port = server_sock.getsockname()[1]
uuid = "94c7ff62-9a81-4a30-88a4-ae8485c328b6"
advertise_service( server_sock, "SampleServer",
                   service_id = uuid,
                   service_classes = [ uuid, SERIAL_PORT_CLASS ],
                   profiles = [ SERIAL_PORT_PROFILE ],
#                   protocols = [ OBEX_UUID ]
                    )
j.debug("Waiting for connection on RFCOMM channel " + str(port))
client_sock, client_info = server_sock.accept()
client_sock.settimeout(.005)
j.debug("Accepted connection")
re2.set()
ge = threading.Event()
gt = threading.Thread(name='greenslow', target=a.flashLed, args=(ge,1,"green"))
gt.daemon = True
gt.start()
a.wait4button()
ge.set()
ge2 = threading.Event()
gt2 = threading.Thread(name='greenfast', target=a.flashLed, args=(ge2,.1,"green"))
gt2.daemon = True
gt2.start()

j.debug("start streaming")
stre = threading.Event()
strt = threading.Thread(name='streaming', target=a.streaming, args=(stre,))
strt.daemon = True
strt.start()

time.sleep(.005)
sett = threading.Thread(name='setpsi', target=a.setpsi)
sett.daemon = True
sett.start()
while True:
	try:
		msg = client_sock.recv(1024)
		if len(msg) != 0:
			j.debug(msg)
			a.psi = float(msg)
			a.go = True
			msg = ''
	except BluetoothError,e:
		if e.args[0] != "timed out": #.recv() blocks or gives this error, we'll ignore it and hope it's not a problem
    			j.error("Unexpected bluetooth error:", sys.exc_info()[0])
    			print("Unexpected bluetooth error:", sys.exc_info()[0])

			break
	except KeyboardInterrupt:
		raise
		break
	except:
		raise
    		break
j.info("disconnected")
GPIO.cleanup()
ge2.set()
stre.set()
client_sock.close()
server_sock.close()
sys.exit()
j.info("all done")

