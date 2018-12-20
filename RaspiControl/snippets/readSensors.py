#!/usr/bin/env python
import numpy as np
import time
import threading
import Adafruit_ADS1x15
from mpu6050 import mpu6050


class Sensors(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self._stop_event = threading.Event()

        self.adc = Adafruit_ADS1x15.ADS1115()
        self.mpu = mpu6050(0x68)

        # can change gain to 2, but won't read over 200psi, would need to remake calibration curve
        self.GAIN = 1
        self.alpha = .02
        self.dt = .01
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

    def run(self):
        while not self._stop_event.is_set():
            self.readsensors()

    def set_stop_event(self):  # sets a flag to kill this Thread.
        self._stop_event.set()


if __name__ == "__main__":

    time.sleep(2)
    sensor = Sensors()
    sensor.setDaemon(True)
    sensor.start()
    readhistx = [0] * 1000
    readhisty = [0] * 1000
    try:
        while True:
            time.sleep(.1)
            readx = sensor.angles[0]
            readhistx.insert(0, readx)
            readhistx.pop()
            ready = sensor.angles[1]
            readhisty.insert(0, ready)
            readhisty.pop()
            print(readx, ready)
    finally:
        sensor.set_stop_event()
        sensor.join()
        import matplotlib
        import matplotlib.pyplot as plt
        matplotlib.use('Agg')
        plt.plot(readhistx)
        print("here")