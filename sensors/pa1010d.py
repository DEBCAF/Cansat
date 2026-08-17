from machine import I2C, Pin
import pa1010dconfig
from time import sleep
    
i2c = I2C(0, scl=Pin(5), sda=Pin(4))  # Adjust pins as needed
gps = PA1010D(i2c)

while True:
    lat, lon = gps.get_coordinates()
    if lat and lon:
        print(f"Latitude: {lat}, Longitude: {lon}")
    else:
        print("Waiting for GPS fix...")
    utime.sleep(1)
