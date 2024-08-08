from lib.lora_e220 import LoRaE220, print_configuration, Configuration
from Pin import Pin
from auxController import AuxController
import serial
import time
from lora_e220_operation_constant import ResponseStatusCode, ModeType

# Configure the serial port
serial_port = '/dev/ttyUSB0'  
baud_rate = 9600

aux_controller = AuxController('up')

m1_pin = "red_cntrl"
m0_pin = "green_cntrl"

#Pin(m1_pin,0)
#Pin(m0_pin,0)

#uart = serial.Serial(serial_port, baud_rate)
lora = LoRaE220('900T22D', aux_pin=aux_controller, m0_pin=m0_pin, m1_pin=m1_pin)
lora.set_mode(ModeType.MODE_0_NORMAL)
time.sleep(1)

code = lora.begin()
print(code)
print(f"Initialization: {ResponseStatusCode.get_description(code)}")


print("Custom configuration..")
custom_conf = Configuration(lora.model)
custom_conf.set_custom_conf()
code_custom, configuration_custom = lora.set_configuration(custom_conf)
print("Custom configuration done!")
print_configuration(configuration_custom)




code, configuration = lora.get_configuration()

print("Retrieve configuration: {}", ResponseStatusCode.get_description(code))
print_configuration(configuration)

lora.send_transparent_message('ceren')
print("Sent message!")
    
'''
while True:
    lora.send_transparent_message('ceren')
    print("Sent message!")
    time.sleep(5)
'''   


