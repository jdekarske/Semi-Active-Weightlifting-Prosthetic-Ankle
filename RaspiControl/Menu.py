#!/usr/bin/env python
import time
import RPi.GPIO as GPIO
import Outputs
import Utils
GPIO.setmode(GPIO.BOARD)
GPIO.setwarnings(False)


class Menu:
    def __init__(self):
        self.led = None
        self.sensor = None
        self.bluetoothsetup = None
        self.bluetooth = None
        self.activemenu = 0
        self.valves = None
        self.button = 16
        self.psiflag = False
        self.newpsi = 20
        GPIO.setup(self.button, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    def wait4button(self):  # complicated way to discern between holds and presses
        pressed = False
        print("waiting")
        time.sleep(0.01)
        GPIO.wait_for_edge(self.button, GPIO.FALLING, bouncetime=200)
        timepressed = time.clock()
        while not pressed:
            if GPIO.input(self.button):
                pressed = True
        if time.clock() > (timepressed + 1.0):
            return True  # held
        else:
            return False  # press

    def startup(self):
        self.led = Outputs.LED()
        self.led.setDaemon(True)
        self.led.set_status("startup", True)
        self.led.start()
        self.sensor = Utils.Sensors()
        self.sensor.setDaemon(True)
        self.sensor.start()
        self.bluetoothsetup = Utils.BluetoothSetup()
        self.valves = Outputs.Valves(getpressure_function=self.sensor.get_pressures)
        self.valves.setDaemon(True)
        self.valves.start()
        self.led.set_status("startup", False)

    def loop(self):
        while True:
            while not self.psiflag:  # check if there is a new desired pressure from the app
                self.led.set_menu(0)
                try:
                    connected = self.bluetooth.isAlive()  # see if bluetooth is initiated yet
                except AttributeError:
                    connected = False
                if not connected:  # if bluetooth is connected, skip this menu option
                    if self.wait4button():  # wait here for user input
                        print('connecting')
                        self.led.set_status("connecting", True)
                        self.bluetoothsetup.createnewsocket() #initiate connection
                        self.bluetooth = Utils.Stream(clientsocket_function=self.bluetoothsetup.getclientsocket,
                                                      getangle_function=self.sensor.get_angles,
                                                      getpressure_function=self.sensor.get_pressures)
                        self.valves.setbluetoothfunction(self.bluetooth.get_update)
                        self.bluetooth.setDaemon(True)
                        self.bluetooth.start()
                        self.led.set_status("connecting", False)
                self.led.set_menu(1)
                if self.wait4button():  # TODO: calibrate
                    print("calibrate")
                self.led.set_menu(2)
                if self.wait4button():  # TODO: switch between walking/lifting mode from button push
                    print("walking")
            self.valves.setpressure(self.newpsi)  # If there is a new desired pressure, do this

    def killthreads(self):
        self.sensor.set_stop_event()
        self.sensor.join(.1)
        self.bluetooth.set_stop_event()
        self.bluetooth.join(.1)
        self.led.set_stop_event()
        self.led.join()


if __name__ == "__main__":
    main = Menu()
    main.startup()
    # try:
    main.loop()
    # finally:
    #    main.killthreads()