# file: rfcomm-server.py
# auth: Albert Huang <albert@csail.mit.edu>
# desc: simple demonstration of a server application that uses RFCOMM sockets
# mostly jason
# $Id: rfcomm-server.py 518 2007-08-10 07:20:07Z albert $
import numpy as np
from bluetooth import *
from readADC import readADC
import time
import sys
import RPi.GPIO as GPIO
import threading
import sys

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

	def wait4button(self):
		GPIO.wait_for_edge(self.button, GPIO.RISING)
		print("button press")

        def activate(self,item,sec): #do this without sleeping, this probably sucks anyway
                try:
                        if type(sec) is not int:
                                print("must be a time in seconds")
                        elif sec < 0:
                                sec = 0
                        elif sec > 10:
                                sec = 10
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
                                print("incorrect item")
                        GPIO.output(v,GPIO.HIGH)
                        time.sleep(sec)
                        GPIO.output(v,GPIO.LOW)

                except:
                        print("Unexpected GPIO error:", sys.exc_info()[0])
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
                                print("incorrect item")
                        if on:
                                GPIO.output(v,GPIO.HIGH)
                        elif on == 0:
                                GPIO.output(v,GPIO.LOW)
                        elif on == 3: #indicates processing, probably a poor way to do so
                                GPIO.output(v,GPIO.HIGH)
                                time.sleep(.01)
                                GPIO.output(v,GPIO.LOW)
                        else:
                                print("incorrect command")
                except:
                        print("Unexpected GPIO error:", sys.exc_info()[0])
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
			print("invalid color")
			raise
		while not e.isSet():
                	GPIO.output(self.c,GPIO.HIGH)
                	time.sleep(t)
                	event_is_set = e.is_set()
                	if event_is_set:
                	    	print('stop led from flashing')
                	else:
                	    	GPIO.output(self.c,GPIO.LOW)
                	    	time.sleep(t)
	def setpsi(set):
		pass
a=outputs()

re = threading.Event()
rt = threading.Thread(name='daemon', target=a.flashLed, args=(re,.5,"red"))
rt.start()

a.wait4button()

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
print("Waiting for connection on RFCOMM channel %d" % port)
client_sock, client_info = server_sock.accept()
client_sock.settimeout(.005)
print("Accepted connection from ", client_info)
re.set()
ge = threading.Event()
gt = threading.Thread(name='daemon', target=a.flashLed, args=(ge,.5,"green"))
gt.start()
a.wait4button()

#for smoothing need to add a function
max_samples = 20
p0 = []
p1 = []
p2 = []
p3 = []

while True:
	try:
		read = readADC()
		p0 = np.append(p0,read[0]) #make this better
		p1 = np.append(p1,read[1])
		#p2 = np.append(p2,read[2]) #don't need these for now
		#p3 = np.append(p3,read[3])
		meanp0 = np.mean(p0)
		meanp1 = np.mean(p1)
		#meanp2 = np.mean(p2)
		#meanp3 = np.mean(p3)
		client_sock.send(str(round(meanp0,1))+'/'+str(round(meanp1,1))) #+'/'+str(round(meanp2,1))+'/'+str(round(meanp3,1)))

		if len(p0) == max_samples:
    			p0 = np.delete(p0, 0)
    			p1 = np.delete(p1, 0)
    			#p2 = np.delete(p2, 0)
    			#p3 = np.delete(p3, 0)

		msg = client_sock.recv(1024)
		if len(msg) != 0:
			print(msg)
			psi = message


	except BluetoothError,e:
		if e.args[0] != "timed out": #.recv() blocks or gives this error, we'll ignore it and hope it's not a problem
    			print("Unexpected bluetooth error:", sys.exc_info()[0])
			print(e)
			break
	except KeyboardInterrupt:
		break
	except:
    		print("Unexpected error:", sys.exc_info()[0])
		pass
print("disconnected")
client_sock.close()
server_sock.close()
sys.exit()
print("all done")

