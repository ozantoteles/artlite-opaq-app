from Pin import Pin
import time

m1_pin = "blue_cntrl"
m0_pin = "green_cntrl"

m1 = Pin(m1_pin)
m0 = Pin(m0_pin)

m1.on()
time.sleep(2)
m1.off()
time.sleep(2)

m0.on()
time.sleep(2)
m0.off()
time.sleep(2)