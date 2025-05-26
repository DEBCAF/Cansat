from machine import I2C, Pin
import tsl2591config
from time import sleep

# Initialize I2C
i2c = I2C(0, scl=Pin(5), sda=Pin(4))  # Adjust pins as per your setup

# Initialize TSL2591 sensor
tsl2591 = tsl2591config.TSL2591(i2c)

# Loop to read sensor data
while True:
    full_spectrum = tsl2591.get_full_spectrum()
    infrared = tsl2591.get_infrared()
    visible_light = tsl2591.get_visible_light()

    print(f"Full Spectrum: {full_spectrum} | Infrared: {infrared} | Visible: {visible_light}")
    sleep(1)