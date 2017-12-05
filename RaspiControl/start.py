import RPi.GPIO as GPIO
import time
import io
import numpy as np
import logging
import subprocess

global menuv
menuv = 0
global buttonpress
buttonpress = 0
global buttonhold
buttonhold = 0

#logging setup
logging.basicConfig(format='\n%(asctime)s %(message)s', filename='/home/pi/semi-active-weightlifting-prosthetic-ankle/RaspiControl/data.log',level=logging.DEBUG)
logging.info('----Startup----')

#pin setup
GPIO.setmode(GPIO.BOARD) # Use board pin numbering
button   = 36
ledr = 33
ledg = 35
ledb = 37
GPIO.setup(button, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(ledr, GPIO.OUT) #for RGB LED
GPIO.setup(ledg, GPIO.OUT)
GPIO.setup(ledb, GPIO.OUT)

def blink(color):
        GPIO.output(color,True)
        time.sleep(.1)
        GPIO.output(color,False)
        time.sleep(.1)

def onbuttonpress(channel):
    global menuv
    global buttonhold
    global buttonpress
    time.sleep(1)
    buttonpress = 1 # button is pressed
    if(GPIO.input(button) == 0):
        buttonhold = 1 # button is held
    else:
        menuv += 1

GPIO.add_event_detect(button, GPIO.FALLING, bouncetime=300, callback=onbuttonpress)

def menu():
    global menuv
    global buttonhold
    buttonhold = 0
    while(True):
        while(menuv == 0):
            if(buttonhold): #pair
                buttonhold = 0
                logging.info('pairing...')
                print("pair") #pair()
            blink(ledr)
        while(menuv == 1): #calibrate
            if(buttonhold):
                buttonhold = 0
                logging.info('calibrating...')
                print("calibrate") #calibrate()
            blink(ledg)
        while(menuv == 2): #ankle active
            if(buttonhold):
		buttonhold = 0
		print("anklemodel") #anklemodel()
            blink(ledb)
        while(menuv == 3): #exit
            blink(ledg)
       	    blink(ledb)
            if(buttonhold):
                logging.info('exiting...')
                menuv = 10
        if(buttonhold):
            break
        else:
            menuv = 0

#start stuff
menu()

#cleanup
GPIO.cleanup()
logging.info('----Finish----')
subprocess.call(['shutdown', '-h', 'now'], shell=False)
