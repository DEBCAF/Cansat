from micropython import const
import utime

# Default I2C address for PA1010D GPS
PA1010D_I2C_ADDR = const(0x10)

# NMEA Sentence Types
NMEA_GGA = "GGA"
NMEA_RMC = "RMC"

class PA1010D:
    def __init__(self, i2c, addr=PA1010D_I2C_ADDR):
        self.i2c = i2c
        self.addr = addr

    def _read_sentence(self):
        """Reads a line from the PA1010D GPS over I2C."""
        try:
            data = self.i2c.readfrom(self.addr, 255)  # Read up to 255 bytes
            return data.decode('utf-8').strip()
        except Exception as e:
            return ""

    def get_nmea_sentence(self, sentence_type):
        """Fetches the latest NMEA sentence of the specified type."""
        for _ in range(10):  # Try up to 10 times
            sentence = self._read_sentence()
            if sentence and sentence_type in sentence:
                return sentence
            utime.sleep(0.1)  # Small delay before next attempt
        return None

    def get_gga(self):
        """Returns the latest GGA sentence (latitude, longitude, altitude)."""
        return self.get_nmea_sentence(NMEA_GGA)

    def get_rmc(self):
        """Returns the latest RMC sentence (time, date, speed, course)."""
        return self.get_nmea_sentence(NMEA_RMC)

    def get_coordinates(self):
        """Parses the latest GGA sentence and returns latitude and longitude."""
        gga = self.get_gga()
        if not gga:
            return None, None
        try:
            parts = gga.split(',')
            lat = self._convert_to_degrees(parts[2], parts[3])
            lon = self._convert_to_degrees(parts[4], parts[5])
            return lat, lon
        except:
            return None, None

    def _convert_to_degrees(self, value, direction):
        """Converts GPS coordinate format from DDDMM.MMMM to decimal degrees."""
        if not value:
            return None
        degrees = float(value[:2]) + float(value[2:]) / 60.0
        if direction in ('S', 'W'):
            degrees = -degrees
        return degrees

    