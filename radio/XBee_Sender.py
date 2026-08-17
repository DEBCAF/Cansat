import machine
import utime
from machine import UART
from machine import Pin
count = 0

txpin = Pin(12, Pin.OUT)
rxpin = Pin(13, Pin.IN)


#Initialise UART for XBee Communication
uart = UART(0, tx=txpin, rx=rxpin, baudrate=9600)

def send_data(data):
    try:
        # Send the message over UART
        uart.write(data)
        
        # Debugging output to console
        print("Sent: " + data)
    except OSError as e:
        print("Failed to send")
    
    utime.sleep(1)
while True:
    count = count + 1
    send_data("Hello "+str(count))