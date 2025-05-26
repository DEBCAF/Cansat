from micropython import const

# TSL2591 default I2C address
TSL2591_ADDR = const(0x29)

# TSL2591 Registers
REG_ENABLE = const(0x00)      # Enable register
REG_CONTROL = const(0x01)     # Control register
REG_STATUS = const(0x13)      # Status register
REG_CHAN0_LOW = const(0x14)   # Full-spectrum light data low byte
REG_CHAN1_LOW = const(0x16)   # Infrared light data low byte

# TSL2591 Command Bits
COMMAND_BIT = const(0xA0)

# Enable Register Values
POWER_ON = const(0x01)        # Power on sensor
ALS_ENABLE = const(0x02)      # Enable ambient light sensing

# Integration Time and Gain Settings
GAIN_LOW = const(0x00)        # Low gain setting
INTEGRATION_TIME_100MS = const(0x00)  # 100ms integration time


class TSL2591:
    def __init__(self, i2c):
        """Initialize the TSL2591 sensor over I2C."""
        self.i2c = i2c
        self.initialize()

    def write_register(self, register, value):
        """Write a byte to a specific register."""
        self.i2c.writeto_mem(TSL2591_ADDR, COMMAND_BIT | register, bytes([value]))

    def read_register(self, register, length=1):
        """Read bytes from a specific register."""
        return self.i2c.readfrom_mem(TSL2591_ADDR, COMMAND_BIT | register, length)

    def initialize(self):
        """Initialize the TSL2591 sensor."""
        # Power on and enable ALS
        self.write_register(REG_ENABLE, POWER_ON | ALS_ENABLE)
        # Set gain and integration time
        self.write_register(REG_CONTROL, GAIN_LOW | INTEGRATION_TIME_100MS)

    def read_luminosity(self):
        """Read full-spectrum and infrared luminosity from the sensor."""
        # Read channel 0 (full spectrum) and channel 1 (infrared)
        ch0_data = self.read_register(REG_CHAN0_LOW, 2)
        ch1_data = self.read_register(REG_CHAN1_LOW, 2)

        # Combine the two bytes to form a 16-bit value
        ch0 = int.from_bytes(ch0_data, 'little')
        ch1 = int.from_bytes(ch1_data, 'little')

        return ch0, ch1

    def get_full_spectrum(self):
        """Get full-spectrum light intensity."""
        ch0, _ = self.read_luminosity()
        return ch0

    def get_infrared(self):
        """Get infrared light intensity."""
        _, ch1 = self.read_luminosity()
        return ch1

    def get_visible_light(self):
        """Get visible light intensity (full spectrum - infrared)."""
        full_spectrum, infrared = self.read_luminosity()
        return full_spectrum - infrared