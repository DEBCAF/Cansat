from machine import I2C, Pin, reset
import time
from scd41config import SCD41

def initialize_i2c():
    """Initialize I2C with proper frequency"""
    i2c = I2C(0, scl=Pin(5), sda=Pin(4))
    devices = i2c.scan()
    print("I2C devices found:", [hex(d) for d in devices])
    return i2c

def main():
    print("Initializing I2C...")
    i2c = initialize_i2c()
    
    if 0x62 not in i2c.scan():
        print("SCD41 not found!")
        return
    
    print("SCD41 found, initializing...")
    
    # Create sensor instance
    scd41 = SCD41(i2c)
    
    # Wait for sensor to be ready
    time.sleep(2)
    
    # First try single shot measurement
    print("Taking single shot measurement...")
    if scd41.measure_single_shot():
        print(f"CO2: {scd41.co2} ppm")
        print(f"Temperature: {scd41.temperature:.1f}°C")
        print(f"Humidity: {scd41.humidity:.1f}%")
    else:
        print("Single shot measurement failed")
    
    print("\nStarting periodic measurements...")
    scd41.start_periodic_measurement()
    
    # Wait for first measurement
    time.sleep(5)
    
    measurement_count = 0
    retry_count = 0
    
    try:
        while True:
            if scd41.read_measurement():
                measurement_count += 1
                retry_count = 0
                print(f"\nMeasurement #{measurement_count}")
                print(f"CO2: {scd41.co2} ppm")
                print(f"Temperature: {scd41.temperature:.1f}°C")
                print(f"Humidity: {scd41.humidity:.1f}%")
            else:
                retry_count += 1
                print(".", end="")
                if retry_count > 10:
                    print("\nToo many retries, restarting sensor...")
                    scd41.stop_periodic_measurement()
                    time.sleep(1)
                    scd41.start_periodic_measurement()
                    retry_count = 0
                    
            time.sleep(2)
    
    except KeyboardInterrupt:
        print("\nStopping measurements...")
        scd41.stop_periodic_measurement()
    
    except Exception as e:
        print(f"Error occurred: {e}")
        scd41.stop_periodic_measurement()

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Fatal error: {e}")
        time.sleep(1)
        reset()  # Reset the device if fatal error occurs