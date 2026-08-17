from machine import Pin,I2C
import adxl345config
import time

i2c = I2C(0, scl=Pin(5),sda=Pin(4))
adx = adxl345config.ADXL345(i2c)

while True:
    x=adx.xValue
    y=adx.yValue
    z=adx.zValue
    print('The acceleration info of x, y, z are:%d,%d,%d'%(x,y,z))
    roll,pitch = adx.RP_calculate(x,y,z)
    print('roll=',roll)
    print('pitch=',pitch)
    time.sleep(1)