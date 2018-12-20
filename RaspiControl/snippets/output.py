#!/usr/bin/env python
import time
import RPi.GPIO as GPIO
import threading


class outputs:
    def __init__(self):
        threading.Thread.__init__(self)
        # valves
        # self.atm = 23
        # self.tores = 29
        # self.tocyl = 31
        # self.valves = [self.atm, self.tores, self.tocyl]
        # leds
        # self.button = 36

        # GPIO.setup(self.button, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        # GPIO.setup(self.valves, GPIO.OUT, initial=GPIO.LOW)
        GPIO.setup(self.leds, GPIO.OUT, initial=GPIO.LOW)

class LED(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        GPIO.setmode(GPIO.BOARD)
        self.ledr = 33
        self.ledg = 37
        self.ledb = 35
        self.leds = [self.ledr, self.ledg, self.ledb]
        GPIO.setup(self.leds, GPIO.OUT, initial=GPIO.LOW)
        self.systemstatus = 'stopped'

    def flash(self):
        self.systemstatus = get_state()
        if self.systemstatus[0]
            if color == "red":
                v = self.ledr
            elif color == "green":
                v = self.ledg
            elif color == "blue":
                v = self.ledb
            else:
                j.error("incorrect color id")
            if on:
                GPIO.output(v, GPIO.HIGH)
            elif on == 0:
                GPIO.output(v, GPIO.LOW)
            elif on == 3:  # indicates processing, probably a poor way to do so
                GPIO.output(v, GPIO.HIGH)
                time.sleep(.01)
                GPIO.output(v, GPIO.LOW)
            else:
                j.error("incorrect led command")
        except:
            j.error("Unexpected GPIO error:" + sys.exc_info()[0])
            GPIO.cleanup()
            raise

    def flashLed(self, e, t, color):

    # flash the specified led every half second
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
        GPIO.output(self.c, GPIO.HIGH)
        time.sleep(t)
        event_is_set = e.is_set()
        if event_is_set:
    break
    else:
    GPIO.output(self.c, GPIO.LOW)
    time.sleep(t)

    def run(self):
        while not self._stop_event.is_set():
            self.activate()

    def set_stop_event(self):  # sets a flag to kill this Thread.
        self._stop_event.set()