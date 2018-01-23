# file: rfcomm-server.py
# auth: Albert Huang <albert@csail.mit.edu>
# desc: simple demonstration of a server application that uses RFCOMM sockets
#
# $Id: rfcomm-server.py 518 2007-08-10 07:20:07Z albert $
import numpy as np
from bluetooth import *
from time import *
import jlogging as j


def pair():
	#bluetooth setup
	server_sock=BluetoothSocket( RFCOMM )
	server_sock.bind(("",PORT_ANY))
	server_sock.listen(1)

	port = server_sock.getsockname()[1]

	uuid = "94c7ff62-9a81-4a30-88a4-ae8485c328b6"
	j.debug(uuid)

	advertise_service( server_sock, "SampleServer",
	                   service_id = uuid,
	                   service_classes = [ uuid, SERIAL_PORT_CLASS ],
	                   profiles = [ SERIAL_PORT_PROFILE ],
	#                   protocols = [ OBEX_UUID ]
	                    )
	j.info("Waiting for connection on RFCOMM channel %d".format(port))
	print("Waiting for connection on RFCOMM channel %d".format(port))

	client_sock, client_info = server_sock.accept()
	client_sock.settimeout(.005)
	j.info("Accepted connection from %s".format(client_info))
	print("Accepted connection from ", client_info)

	return client_sock, server_sock, client_info
