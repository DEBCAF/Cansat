from pm25config import PM25Sensor
from time import sleep

# Initialize PM2.5 Sensor on UART1 (TX: GPIO8, RX: GPIO9)
pm25_sensor = PM25Sensor(uart_id=1, tx=8, rx=9)

while True:
    pm25_value = pm25_sensor.read_data()
    if pm25_value is not None:
        print(f"PM2.5 Concentration: {pm25_value} µg/m³")
    else:
        print("No valid data received. Check wiring or baud rate.")
    sleep(2)  # Read every 2 seconds