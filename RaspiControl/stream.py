# file: rfcomm-server.py
# auth: Albert Huang <albert@csail.mit.edu>
# desc: simple demonstration of a server application that uses RFCOMM sockets
#
# $Id: rfcomm-server.py 518 2007-08-10 07:20:07Z albert $
import numpy as np
from bluetooth import *
from readADC import readADC
from time import *
import sys

def stream(server_sock,client_sock,client_info):
	global setpsi
	global menuv
	menuv = 2
	#for smoothing need to add a function
	max_samples = 20
	p0 = []
	p1 = []
	p2 = []
	p3 = []
	while menuv == 2:
		print(".")
		try:
			read = readADC()
			p0 = np.append(p0,read[0]) #make this better
			p1 = np.append(p1,read[1])
			p2 = np.append(p2,read[2])
			p3 = np.append(p3,read[3])
			meanp0 = np.mean(p0)
			meanp1 = np.mean(p1)
			meanp2 = np.mean(p2)
			meanp3 = np.mean(p3)
			client_sock.send(str(round(meanp0,1))+'/'+str(round(meanp1,1))+'/'+str(round(meanp2,1))+'/'+str(round(meanp3,1)))

			if len(p0) == max_samples:
	    			p0 = np.delete(p0, 0)
	    			p1 = np.delete(p1, 0)
	    			p2 = np.delete(p2, 0)
	    			p3 = np.delete(p3, 0)

			msg = client_sock.recv(1024)
			if len(msg) != 0:
				print(msg)
				setpsi = msg
		except BluetoothError,e:
			if e.args[0] != "timed out": #.recv() blocks or gives this error, we'll ignore it and hope it's not a problem
	    			print("Unexpected bluetooth error:", sys.exc_info()[0])
				print(e)
				break
		except KeyboardInterrupt:
			break
		except:
	    		print("Unexpected stream error:", sys.exc_info()[0])
			print("disconnected")
			client_sock.close()
			server_sock.close()
			print("all done")
	    		break
