# Function to read the 16bit I2C ADC ADS1115
import numpy as np
import Adafruit_ADS1x15


# Create an ADS1115 ADC (16-bit) instance.
adc = Adafruit_ADS1x15.ADS1115()

#can change to 2, but won't read over 200, would need to recalibrate
GAIN = 1
# Call function from other script
def readADC():
    # Read all the ADC channel values in a list.
    values = [0]*4
    for i in range(4):
        # Read the specified ADC channel using the previously set gain value.
        values[i] = adc.read_adc(i, gain=GAIN)
    a_values = np.array(values)
    # convert to psi, see labarchives for calibration
    pressures = .0156*a_values-49.715
    return pressures
