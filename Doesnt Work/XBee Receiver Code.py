# Receiver Code
# Import libraries
from digi.xbee.devices import XBeeDevice
from digi.xbee.models.address import XBee64BitAddress

# Set the correct serial port and baud rate for the XBee
serial_port = "/dev/ttyS0"  
baud_rate = 9600  

# Open the XBee device
device = XBeeDevice(serial_port, baud_rate)

# Open the device connection 
device.open()

# Callback function to handle incoming data
def data_receive_callback(xbee_message):
    # Access the actual data from the XBeeMessage object
    data = xbee_message.data
    print(f"Received data: {data.decode()}")

# Add callback for data reception
device.add_data_received_callback(data_receive_callback)

# Keep the receiver running to listen for incoming data
print("Listening for incoming data... Press Ctrl+C to exit.")
try:
    while True:
        pass
except KeyboardInterrupt:
    print("Receiver stopped.")

# Close the device connection after stopping the receiver
device.close()