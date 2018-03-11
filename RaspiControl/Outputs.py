#!/usr/bin/env python
import time
import RPi.GPIO as GPIO
import threading
GPIO.setmode(GPIO.BOARD)
GPIO.setwarnings(False)


class Valves:
    def __init__(self):
        pass
        # valves
        # self.atm = 23
        # self.tores = 29
        # self.tocyl = 31
        # self.valves = [self.atm, self.tores, self.tocyl]
        # leds
        # self.button = 7

        # GPIO.setup(self.button, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        # GPIO.setup(self.valves, GPIO.OUT, initial=GPIO.LOW)


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
    lights = LED()
    lights.setDaemon(True)
    lights.start()
    lights.set_status("startup", True)
    print("startup")
    time.sleep(15)
    lights.set_status("startup", False)
    lights.set_status("error", True)
    print("error")
    time.sleep(15)
    lights.set_status("error", False)
    lights.set_status("low pressure", True)
    print("low pressure")
    time.sleep(15)
    lights.set_status("low pressure", False)
    for fmenu in [0, 1, 2]:
        print(fmenu)
        lights.set_menu(fmenu)  # "f"status because PEP gives a shadow error and I don't like squigly lines
        lights.set_status("connecting", True)
        lights.set_status("calibrating", True)
        lights.set_status("walking", True)
        time.sleep(5)
        lights.set_status("connecting", False)
        lights.set_status("calibrating", False)
        lights.set_status("walking", False)
        time.sleep(5)
    lights.set_stop_event()