#set up logging across all scripts
from logging import *

basicConfig(format='\n%(asctime)s %(message)s', filename='data.log',level=DEBUG)
info('----Startup----')
