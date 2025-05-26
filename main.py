# Here lies the draft to the final deployment code for CanSat
# by Andrew Wong 2025

from machine import I2C, Pin
from time import sleep
from micropython import const
from scd41config import SCD41
from pm25config import PM25Sensor
import utime
import bmp280config
import adxl345config
import ltr390config
import pa1010dconfig
import tsl2591config
import machine
import csv_setup
from machine import UART

# XBee initialisation things
uart = UART(0, baudrate=9600)



def send_data(data):
    try:
        uart.write(data)
        
        print("Sent: "+data)
    except OSError as e:
        print("Failed to send")
        
#local storage initialisation
data_list = ["cycle","gps_attitude","temperature","pressure","uv_index","ambient_light","gps_location","co2","SCD_41_temperature"
             ,"humidity","TSL2591_full_spectrum","TSL2591_infra_red","TSL2591_visiblle","pm2.5"]
cansat_writer = csv_setup.cansat_csv(data_list)


# I2C initialisation things
i2c = I2C(0, scl=Pin(5),sda=Pin(4))
i2c1 = I2C(1, scl=Pin(3), sda=Pin(2))

# I2C debugging things
devices = i2c.scan()
if devices:
    print("I2C devices found:", [hex(device) for device in devices])
else:
    print("No I2C devices found. Check wiring and connections.")
    
# Sensor initialisation things
adx = adxl345config.ADXL345(i2c1)
bmp = bmp280config.BMP280(i2c)
bmp.oversample_temp = 2
bmp.oversample_pres = 16
ltr = ltr390config.LTR390(i2c) # Please note that this uses a different I2C bus, hence the i2c1
ltr.set_measure_rate(32, 3)  
ltr.set_gain(3)
gps = pa1010dconfig.PA1010D(i2c)
scd41 = SCD41(i2c)
tsl2591 = tsl2591config.TSL2591(i2c)
pm25_sensor = PM25Sensor(uart_id=1, tx=8, rx=9) # Different UART initialisation from XBee 

# Variable initialisation 
measurement_count = 0
retry_count = 0
count = 0

# Confirming that everything is working fine
send_data("Commencing data transmission...")
send_data("Taking single shot measurement...")
utime.sleep(1)
if scd41.measure_single_shot():
    send_data(f"CO2: {scd41.co2} ppm")
    send_data(f" Temperature: {scd41.temperature:.1f}°C")
    send_data(f" Humidity: {scd41.humidity:.1f}%")
else:
    send_data("Single shot measurement failed")
utime.sleep(1)
send_data("Starting periodic measurements...")
utime.sleep(1)

# Starting periodic measurement
scd41.start_periodic_measurement()

# Waiting for all sensors to start up before sending any data
utime.sleep(5)

# Main loop
while True:
    # Confirming which data cycle this is
    count = count + 1
    send_data(str("Sending data cycle: "+str(count)))
    utime.sleep(1)
    
    # ADXL345
    x=adx.xValue
    y=adx.yValue
    z=adx.zValue
    roll,pitch = adx.RP_calculate(x,y,z)
    adxlvalues = f"Acceleration info x = {x} y = {y} z = {z} roll = {roll} pitch = {pitch}"
    send_data(str(adxlvalues))
    utime.sleep(1)
    
    # BMP280
    temperature = bmp.temperature  
    pressure = bmp.pressure        
    bmpvalues = f"Temperature: {temperature:.2f} °C","Pressure:",f"Pressure: {pressure:.2f} hPa"
    send_data(str(bmpvalues))
    utime.sleep(1)
    
    # LTR390
    ltr.set_uvs()  
    sleep(0.1) 
    uv_index = ltr.uvs()
    ltr.set_als()  
    sleep(0.1)  
    als_value = ltr.als()
    ltrvalues = f"UV Index: {uv_index}",f"Ambient Light: {als_value} lux"
    send_data(str(ltrvalues))
    utime.sleep(1)
    
    # PA1010D
    lat, lon = gps.get_coordinates()
    if lat and lon:
        pa1010dvalues = f"Latitude: {lat}, Longitude: {lon}"
        send_data(str(pa1010dvalues))
        utime.sleep(1)
    else:
        pa1010dvalues = "Waiting for GPS fix..."
        send_data(str(pa1010dvalues))
        utime.sleep(1)
        
    # SCD41
    if scd41.read_measurement():
        measurement_count += 1
        retry_count = 0
        scd_co2 = scd41.co2
        scd_temp = scd41.temperature
        scd_humidity = scd41.humidity
        send_data(str(f"Measurement of SCD41: #{measurement_count}"))
        send_data(str(f" CO2: {scd_co2} ppm"))
        send_data(str(f" Temperature: {scd_temp:.1f}°C"))
        send_data(str(f" Humidity: {scd_humidity:.1f}%"))
        utime.sleep(1)
    else:
        retry_count += 1
        send_data(". ")
        utime.sleep(1)
        if retry_count > 10:
            send_data("Too many retries, restarting sensor...")
            utime.sleep(1)
            scd41.stop_periodic_measurement()
            time.sleep(1)
            scd41.start_periodic_measurement()
            retry_count = 0
        
    # TSL2591
    full_spectrum = tsl2591.get_full_spectrum()
    infrared = tsl2591.get_infrared()
    visible_light = tsl2591.get_visible_light()
    tslvalues = f"Full Spectrum: {full_spectrum} | Infrared: {infrared} | Visible: {visible_light}"
    send_data(str(tslvalues))
    utime.sleep(1)
    
    #PM2.5
    pm25_value = pm25_sensor.read_data()
    if pm25_value is not None:
        send_data(f"PM2.5 Concentration: {pm25_value} µg/m³")
    else:
        send_data("No valid data received. Check wiring or baud rate.")
    utime.sleep(2)
    
    #update csv local record
    local_write_list = [count,adxlvalues,temperature,pressure,uv_index,als_value,pa1010dvalues,scd_co2,scd_temp,scd_humidity,
                    full_spectrum,infrared,visible_light,pm25_value]
    cansat_writer.update(local_write_list)
    
    # Confirming the end of a cycle
    send_data(str("End of cycle: "+str(count)))
    utime.sleep(1)
    
    if uart.any():  # Check if data is available
        message = uart.read()  # Read the incoming data
        if message:
            command = message.decode()
            send_data(str("Received on Pico: "+command))  # Decode and print message
            utime.sleep(1)
            if command == "1":
                # Deploy spoilers command here
                send_data("Spoilers Deployed!")
    utime.sleep(1)