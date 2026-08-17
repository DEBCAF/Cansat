from machine import UART
from time import sleep

class PM25Sensor:
    def __init__(self, uart_id=1, tx=8, rx=9, baudrate=9600):
        """Initialize UART for PM2.5 sensor"""
        self.uart = UART(uart_id, baudrate=baudrate, tx=tx, rx=rx)
        self.uart.init(baudrate=baudrate, bits=8, parity=None, stop=1)
        sleep(1)  # Allow sensor to stabilize

    def read_data(self):
        """Reads and parses PM2.5 data from UART."""
        if self.uart.any():  # Check if data is available
            data = self.uart.read(32)  # Read up to 32 bytes
            if data and len(data) >= 10:
                return self.parse_pm25(data)
        return None

    def parse_pm25(self, data):
        """Extracts PM2.5 concentration from sensor data packet."""
        if data[0] == 0x42 and data[1] == 0x4D:  # Valid PM2.5 packet header
            frame_length = (data[2] << 8) | data[3]  # Frame length
            pm25 = (data[6] << 8) | data[7]  # PM2.5 value in µg/m³

            # Verify checksum
            checksum = sum(data[:-2])
            received_checksum = (data[-2] << 8) | data[-1]
            if checksum == received_checksum:
                return pm25  # Return valid PM2.5 value
            else:
                print("Checksum error: Invalid data received.")
        return None  # Return None if invalid