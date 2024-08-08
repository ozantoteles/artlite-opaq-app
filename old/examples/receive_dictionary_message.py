import sys
sys.path.insert(0, "/usr/local/artlite-opaq-app/")
from lib.lora_e220 import LoRaE220, print_configuration, Configuration, BROADCAST_ADDRESS
from Pin import Pin
from auxController import AuxController
import serial
import time
from lora_e220_operation_constant import ResponseStatusCode, ModeType
from lora_e220_constants import FixedTransmission, RssiEnableByte

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

lora = LoRaE220('900T22D', aux_pin=aux_controller, m0_pin=m0_pin, m1_pin=m1_pin)

code = lora.begin()
print("Initialization: {}", ResponseStatusCode.get_description(code))

# Set the configuration to default values and print the updated configuration to the console
# Not needed if already configured
configuration_to_set = Configuration('900T22D')
# Comment this section if you want test transparent trasmission
# configuration_to_set.ADDH = 0x00 # Address of this receive no sender
# configuration_to_set.ADDL = 0x01 # Address of this receive no sender
# configuration_to_set.CHAN = 23 # Address of this receive no sender
# configuration_to_set.TRANSMISSION_MODE.fixedTransmission = FixedTransmission.FIXED_TRANSMISSION
# To enable RSSI, you must also enable RSSI on sender
configuration_to_set.TRANSMISSION_MODE.enableRSSI = RssiEnableByte.RSSI_ENABLED

code, confSetted = lora.set_configuration(configuration_to_set)
print("Set configuration: {}", ResponseStatusCode.get_description(code))

print("Waiting for messages...")
while True:
    if lora.available() > 0:
        # If the sender not set RSSI
        # code, value = lora.receive_dict()
        # If the sender set RSSI
        code, value, rssi = lora.receive_dict(rssi=True)
        print('RSSI: ', rssi)

        print(ResponseStatusCode.get_description(code))

        print(value)
        print(value['key1'])
        time.sleep(2)
