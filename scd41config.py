from micropython import const
from ustruct import unpack as unp, pack
import time

# SCD41 Constants
# Commands
SCD41_CMD_START_PERIODIC = const(0x21B1)
SCD41_CMD_READ_MEASUREMENT = const(0xEC05)
SCD41_CMD_STOP_PERIODIC = const(0x3F86)
SCD41_CMD_MEASURE_SINGLE_SHOT = const(0x219D)
SCD41_CMD_DATA_READY = const(0xE4B8)

class SCD41:
    def __init__(self, i2c_bus, addr=0x62):
        self._i2c = i2c_bus
        self._addr = addr
        self._co2 = 0
        self._temperature = 0
        self._humidity = 0
        
        # Stop any existing measurements
        self.stop_periodic_measurement()
        time.sleep(1)
    
    def _write_command(self, cmd):
        """Write command to the sensor"""
        buffer = bytearray([
            (cmd >> 8) & 0xFF,
            cmd & 0xFF
        ])
        self._i2c.writeto(self._addr, buffer)
    
    def _read_data(self, length):
        """Read data from the sensor"""
        return self._i2c.readfrom(self._addr, length)
    
    def start_periodic_measurement(self):
        """Start periodic measurement mode"""
        self._write_command(SCD41_CMD_START_PERIODIC)
        # First measurement takes longer
        time.sleep(1)
    
    def stop_periodic_measurement(self):
        """Stop periodic measurement mode"""
        self._write_command(SCD41_CMD_STOP_PERIODIC)
        time.sleep(0.5)
    
    def measure_single_shot(self):
        """Perform single measurement"""
        self._write_command(SCD41_CMD_MEASURE_SINGLE_SHOT)
        # Wait for measurement to complete
        time.sleep(5)
        return self.read_measurement()
    
    def data_ready(self):
        """Check if data is ready to be read"""
        self._write_command(SCD41_CMD_DATA_READY)
        time.sleep_ms(1)
        data = self._read_data(3)
        ready = (data[0] << 8) | data[1]
        return ready & 0x7FF
    
    def read_measurement(self):
        """Read measurement data"""
        # Check if data is ready
        if not self.data_ready():
            return False
            
        self._write_command(SCD41_CMD_READ_MEASUREMENT)
        time.sleep_ms(1)
        
        data = self._read_data(9)
        
        # Convert the data
        self._co2 = (data[0] << 8) | data[1]
        temp_raw = (data[3] << 8) | data[4]
        hum_raw = (data[6] << 8) | data[7]
        
        # Convert raw values
        self._temperature = -45 + 175 * temp_raw / 65535
        self._humidity = 100 * hum_raw / 65535
        
        return True
    
    @property
    def co2(self):
        return self._co2
    
    @property
    def temperature(self):
        return self._temperature
    
    @property
    def humidity(self):
        return self._humidity