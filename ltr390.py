from machine import I2C, Pin
from time import sleep
import ltr390config  # Assuming a similar module like bmp280config exists

# Initialize I2C
i2c = I2C(0, scl=Pin(5), sda=Pin(4))  # Adjust pins for your board
devices = i2c.scan()

if devices:
    print("I2C devices found:", [hex(device) for device in devices])
else:
    print("No I2C devices found. Check wiring and connections.")

# Initialize LTR390 sensor
ltr = ltr390config.LTR390(i2c)

# Optional: Set measurement parameters (adjust as needed)
ltr.set_uvs()  # Enable UV Mode
ltr.set_measure_rate(32,3)  # 100ms measurement time
ltr.set_gain(3)  # Set gain (default x3)

# Loop to read sensor data
while True:
    uv_index = ltr.uvs()
    als_value = ltr.als()
    
    print(f"UV Index: {uv_index}")
    print(f"Ambient Light: {als_value} lux")
    print("-" * 30)
    sleep(1)

