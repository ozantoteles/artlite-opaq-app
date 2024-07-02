from lib.lora_e220 import LoRaE220, print_configuration
from Pin import Pin
from auxController import AuxController
import serial
import time
from lora_e220_operation_constant import ResponseStatusCode

# Configure the serial port
serial_port = '/dev/ttyUSB0'  
baud_rate = 9600

aux_controller = AuxController('up')

m1_pin = "blue_cntrl"
m0_pin = "green_cntrl"
# m1 = Pin(m1_pin)
# m0 = Pin(m0_pin)

#uart = serial.Serial(serial_port, baud_rate)

lora = LoRaE220('900T22D', aux_pin=aux_controller, m0_pin=m0_pin, m1_pin=m1_pin)

code = lora.begin()
print(code)
print(f"Initialization: {ResponseStatusCode.get_description(code)}")

code, configuration = lora.get_configuration()

print("Retrieve configuration: {}", ResponseStatusCode.get_description(code))
print_configuration(configuration)