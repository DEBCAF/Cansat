from machine import I2C, Pin
from time import sleep
import bmp280config

# Initialize I2C
i2c = I2C(0,scl=Pin(5), sda=Pin(4))  # Adjust pins for your board
devices = i2c.scan()

if devices:
    print("I2C devices found:", [hex(device) for device in devices])
else:
    print("No I2C devices found. Check wiring and connections.")
# Initialize BMP280 sensor
bmp = bmp280config.BMP280(i2c)

# Optional: Set oversampling (adjust as needed)
bmp.oversample_temp = 2
bmp.oversample_pres = 16

# Loop to read sensor data
while True:
    temperature = bmp.temperature  # Read temperature in °C
    pressure = bmp.pressure        # Read pressure in hPa
    print(f"Temperature: {temperature:.2f} °C")
    print(f"Pressure: {pressure:.2f} hPa")
    print("-" * 30)
    sleep(1)
