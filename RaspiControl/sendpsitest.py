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

	except BluetoothError,e:
		if e.args[0] != "timed out": #.recv() blocks or gives this error, we'll ignore it and hope it's not a problem
    			print("Unexpected bluetooth error:", sys.exc_info()[0])
			print(e)
			break
	except KeyboardInterrupt:
		break
	except:
    		print("Unexpected error:", sys.exc_info()[0])
    		break

print("disconnected")

client_sock.close()
server_sock.close()
print("all done")
