# Sender Code
# import libraries
import serial
import time
from digi.xbee.devices import XBeeDevice, RemoteXBeeDevice, XBee64BitAddress

# assign the button pins and XBee device settings
SERIAL_PORT = "/dev/ttyS0"
BAUD_RATE = 9600

# configure the xbee
xbee = XBeeDevice(SERIAL_PORT, BAUD_RATE)
xbee.open()

# handler for sending data to a receiving XBee device
def send_data(data):
        dest_addr_long = XBee64BitAddress.from_hex_string("0013A20042396DE6")
        remote_device = RemoteXBeeDevice(xbee, dest_addr_long)
        xbee.send_data_async(remote_device, bytes(data, 'utf-8'))
        print("Sent "+data)

# main (for testing)
# choice = "y"
# while choice != "n":
#         data = input("What do you want to send over? ")
#         send_data(data)
#         choice = ""
#         while choice != "y" and choice != "n":
#                 choice = input("Do you want to send another message? (y/n) ")
#                 choice = choice.lower()
# main (for sending continous data)
# try:
#         while True:
#                 send_data(data) # replace data variable with sensor data 
#                 time.sleep(1)
# except KeyboardInterrupt:
#         print("Stopped")
# clean up
xbee.close()