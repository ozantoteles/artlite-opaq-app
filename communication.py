from lib.lora_e220 import LoRaE220, print_configuration, Configuration
from Pin import Pin
from auxController import AuxController
import serial
import time
import json
from lora_e220_operation_constant import ResponseStatusCode, ModeType




# Configure the serial port
serial_port = '/dev/ttyUSB0'  
baud_rate = 9600

aux_controller = AuxController('up')

m1_pin = "red_cntrl"
m0_pin = "green_cntrl"
vcc_pin = "lazer_cntrl"
ftdi_en_pin = "usb2_en"


m1_pin_obj = Pin(m1_pin,0)
m0_pin_obj = Pin(m0_pin,0)
time.sleep(1)
vcc_pin_obj = Pin(vcc_pin,0)
time.sleep(1)
ftdi_en_pin_obj = Pin(ftdi_en_pin,0)
time.sleep(1)
vcc_pin_obj.on()
time.sleep(1)
ftdi_en_pin_obj.on()
time.sleep(5)



#vcc_pin_obj = Pin(vcc_pin,1)
'''

#off
m1_pin_obj = Pin(m1_pin,0)
m0_pin_obj = Pin(m0_pin,0)
ftdi_en_pin_obj = Pin(ftdi_en_pin,0)
vcc_pin_obj = Pin(vcc_pin,0)
i=0
while i<3:
    time.sleep(3)
    vcc_pin_obj.on()
    time.sleep(3)
    vcc_pin_obj.off()
    i+=1
print("CIKTIMM")
#on
vcc_pin_obj.on()
time.sleep(5)
ftdi_en_pin_obj.on()
time.sleep(5)

'''

#uart = serial.Serial(serial_port, baud_rate)
lora = LoRaE220('900T22D', aux_pin=aux_controller, m0_pin=m0_pin, m1_pin=m1_pin)
lora.set_mode(ModeType.MODE_0_NORMAL)
time.sleep(1)

code = lora.begin()
print(code)
print(f"Initialization: {ResponseStatusCode.get_description(code)}")


print("Custom configuration..")
custom_conf = Configuration(lora.model)
custom_conf.set_custom_conf(addh=0x02, addl=0x03, CHAN=25)
code_custom, configuration_custom = lora.set_configuration(custom_conf)
print("Custom configuration done!")
print_configuration(configuration_custom)




code, configuration = lora.get_configuration()

print("Retrieve configuration: {}", ResponseStatusCode.get_description(code))
print_configuration(configuration)

#lora.send_transparent_message('ceren')
#print("Sent message!")
    

'''
while True:
    lora.send_transparent_message('ceren')
    print("Sent message!")
    time.sleep(5)
'''


while True:


    print("Custom configuration..1")
    custom_conf = Configuration(lora.model)
    custom_conf.set_custom_conf(addh=0x02, addl=0x03, CHAN=25)
    code_custom, configuration_custom = lora.set_configuration(custom_conf)
    print("Custom configuration done!")
    print_configuration(configuration_custom)
    data = {'key1': 'value1', 'key2': 'value2'}
    json_data = json.dumps(data)
    print("Length of data being sent:", len(json_data+','))  # Log the length of serialized JSON data
    code = lora.send_transparent_message(json_data)  # Ensure this method sends the serialized JSON data correctly
    print("Send message:", ResponseStatusCode.get_description(code))
    time.sleep(5)
    
    print("Custom configuration..2")
    custom_conf = Configuration(lora.model)
    custom_conf.set_custom_conf(addh=0x01, addl=0x04, CHAN=25)
    code_custom, configuration_custom = lora.set_configuration(custom_conf)
    print("Custom configuration done!")
    print_configuration(configuration_custom)
    data = {'key1': 'value3', 'key2': 'value4'}
    json_data = json.dumps(data)
    print("Length of data being sent:", len(json_data+','))  # Log the length of serialized JSON data
    code = lora.send_transparent_message(json_data)  # Ensure this method sends the serialized JSON data correctly
    print("Send message:", ResponseStatusCode.get_description(code))
    time.sleep(5)

