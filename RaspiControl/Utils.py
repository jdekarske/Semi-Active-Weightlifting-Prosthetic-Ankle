#!/usr/bin/env python
from bluetooth import *
import numpy as np
import time
import threading
import Adafruit_ADS1x15
from mpu6050 import mpu6050


class Sensors(threading.Thread):
    def __init__(self, dt=.001):
        threading.Thread.__init__(self)
        self._stop_event = threading.Event()

        self.adc = Adafruit_ADS1x15.ADS1115()
        self.mpu = mpu6050(0x68)

        # can change gain to 2, but won't read over 200psi, would need to remake calibration curve
        self.GAIN = 1
        self.alpha = .02
        self.dt = dt
        self.lastangle = 0
        self.lasttime = time.clock()
        self.pressures = [20, 20, 20, 20]
        self.angles = [0, 0]

    def readsensors(self):
        if time.clock() > (self.dt + self.lasttime):
            self.lasttime = time.clock()

            accdict = self.mpu.get_accel_data()
            gyrdict = self.mpu.get_gyro_data()
            acc = np.array([accdict["x"], accdict["y"], accdict["z"]])
            gyr = np.array([gyrdict["x"], gyrdict["y"]])
            pitchacc = np.arctan2(acc[1], acc[2]) * 180 / np.pi
            rollacc = np.arctan2(acc[0], acc[2]) * 180 / np.pi
            accnp = np.array([rollacc, pitchacc])

            # complementary filter
            self.angles = (1 - self.alpha)*(self.lastangle+gyr*self.dt) + self.alpha*accnp
            self.lastangle = self.angles

            values = [0]*4
            for i in range(4):
                # Read the specified ADC channel using the previously set gain value.
                values[i] = self.adc.read_adc(i, gain=self.GAIN)
            a_values = np.array(values)
            # convert to psi, see labarchives for calibration
            self.pressures = .0156*a_values-49.715

    def get_pressures(self):
        return self.pressures

    def get_angles(self):
        return self.angles

    def run(self):
        while not self._stop_event.is_set():
            self.readsensors()

    def set_stop_event(self):  # sets a flag to kill this Thread.
        self._stop_event.set()


class BluetoothSetup:
    def __init__(self):
        self.client_sock = None
        self.client_info = None
        self.server_sock = BluetoothSocket(RFCOMM)
        self.server_sock.bind(("", PORT_ANY))
        self.server_sock.listen(1)
        self.port = self.server_sock.getsockname()[1]
        self.uuid = "94c7ff62-9a81-4a30-88a4-ae8485c328b6"
        advertise_service(self.server_sock, "SampleServer",
                          service_id=self.uuid,
                          profiles=[SERIAL_PORT_PROFILE],
                          service_classes=[self.uuid, SERIAL_PORT_CLASS])
        # j.debug("Accepted Connection")

    def getclientsocket(self):
        return self.client_sock

    def createnewsocket(self):

        # j.debug("Waiting for connection on RFCOMM channel " + str(self.port))
        self.client_sock, self.client_info = self.server_sock.accept()
        self.client_sock.settimeout(.005)

    def status(self):
        return self.client_info


class Stream(threading.Thread):
    def __init__(self, clientsocket_function, getpressure_function, getangle_function):
        threading.Thread.__init__(self)
        self.msg = ''
        self._stop_event = threading.Event()
        self.client_sock = clientsocket_function
        self.getpressure = getpressure_function
        self.getangle = getangle_function
        self.max_samples = 10
        self.p0 = []
        self.p1 = []
        self.mean_p0 = 20  # it'll be a bit more than 1 atm, likely
        self.mean_p1 = 20
        self.commandpsi = 20
        self.newpsiflag = False

    def update(self):
        pressures = self.getpressure
        self.p0 = np.append(self.p0, pressures[0])
        self.p1 = np.append(self.p1, pressures[1])
        self.mean_p0 = np.mean(self.p0)
        self.mean_p1 = np.mean(self.p1)
        if len(self.p0) == self.max_samples:
            self.p0 = np.delete(self.p0, 0)
            self.p1 = np.delete(self.p1, 0)
        try:
            self.msg = self.client_sock.recv(1024)
            if len(self.msg) != 0:
                self.commandpsi = float(self.msg)  # PSI FUNCTION HERE
                print(self.commandpsi)
                self.newpsiflag = True
                self.msg = ''
        except BluetoothError, e:  # .recv() blocks or gives this error, we'll ignore it and hope it's not a problem
            if e.args[0] != "timed out":
                print("Unexpected bluetooth error:", sys.exc_info()[0])
                self._stop_event.set()

    def get_commandpsi(self):
        if self.newpsiflag:
            self.newpsiflag = False
            return self.commandpsi

    def send(self):
        try:
            self.client_sock.send('{' + str(round(self.mean_p0, 1)) + '/' + str(
                round(self.mean_p1, 1)) + '}')
        except BluetoothError:
            print('Error: Connection lost')
            self._stop_event.set()

    def run(self):
        try:
            while not self._stop_event.is_set():
                self.update()
                self.send()
        finally:
            self.client_sock.close()

    def set_stop_event(self):  # sets a flag to kill this Thread.
        self.client_sock.close()
        self._stop_event.set()


if __name__ == "__main__":
    sensor = Sensors()
    sensor.setDaemon(True)
    sensor.start()
    print('connecting')
    sockets = BluetoothSetup()
    bluetooth = Stream(clientsocket_function=sockets.getclientsocket(),
                       getangle_function=sensor.get_angles(),
                       getpressure_function=sensor.get_pressures())
    bluetooth.setDaemon(True)
    bluetooth.start()
    try:
        while True:
            time.sleep(1)
            print('streaming')
    finally:
        sensor.set_stop_event()
        sensor.join(0.1)
        bluetooth.set_stop_event()
        bluetooth.join()
