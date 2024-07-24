import sys
sys.path.insert(0, "/usr/local/OPAQ/")
from lib.lora_e220 import LoRaE220, print_configuration, Configuration
from Pin import Pin
from auxController import AuxController
import serial
import time
import json
from lora_e220_operation_constant import ResponseStatusCode, ModeType
from lora_e220_constants import FixedTransmission, RssiEnableByte

import hashlib

def generate_address(unique_id):
    # Hash the unique ID using SHA-256
    hash_object = hashlib.sha256(unique_id.encode())
    # Convert the hash to an integer
    hash_int = int(hash_object.hexdigest(), 16)
    # Take the modulus to fit into the address range 0000-FFFF
    address = hash_int % 0x10000
    # Format as 4-digit hexadecimal
    address_hex = f"{address:04X}"
    return address_hex

def split_address(address):
    # Split the 4-digit hex address into high byte and low byte
    addrh = int(address[:2], 16)
    addrl = int(address[2:], 16)
    return addrh, addrl

unique_id_path = '/tmp/meta_files/UNIQUE_ID/id-displayboard.json'
with open(unique_id_path, 'r') as file:
    unique_id_json_content = file.read()
    unique_id_data = json.loads(unique_id_json_content)

# Extract the unique ID
unique_id = unique_id_data['val']

# Generate the address
address = generate_address(unique_id)

# Split the address into high byte and low byte
addrh, addrl = split_address(address)

# Configure the serial port
serial_port = '/dev/ttyUSB0'  
baud_rate = 9600

aux_controller = AuxController('up')

m1_pin = "red_cntrl"
m0_pin = "green_cntrl"
vcc_pin = "lazer_cntrl"
ftdi_en_pin = "usb2_en"

m1_pin_obj = Pin(m1_pin, 0)
m0_pin_obj = Pin(m0_pin, 0)
vcc_pin_obj = Pin(vcc_pin, 0)
ftdi_en_pin_obj = Pin(ftdi_en_pin, 0)
time.sleep(1)
vcc_pin_obj.on()
time.sleep(1)
ftdi_en_pin_obj.on()
time.sleep(5)

# Initialize LoRa module
lora = LoRaE220('900T22D', aux_pin=aux_controller, m0_pin=m0_pin, m1_pin=m1_pin)

code = lora.begin()
print("Initialization: {}", ResponseStatusCode.get_description(code))

# Set the configuration to default values and print the updated configuration to the console
# Not needed if already configured
configuration_to_set = Configuration('900T22D')
configuration_to_set.ADDL = addrl #0x02 # Address of this sender no receiver
configuration_to_set.TRANSMISSION_MODE.fixedTransmission = FixedTransmission.FIXED_TRANSMISSION
# To enable RSSI, you must also enable RSSI on receiver
configuration_to_set.TRANSMISSION_MODE.enableRSSI = RssiEnableByte.RSSI_ENABLED

code, confSetted = lora.set_configuration(configuration_to_set)
print("Set configuration: {}", ResponseStatusCode.get_description(code))

while True:
    # Send a dictionary message (fixed)
    data = unique_id_json_content #{'key1': 'value1', 'key2': 'value2'}
    code = lora.send_fixed_dict(addrh, addrl, 25, data)
    # The receiver must be configured with ADDH = 0x00, ADDL = 0x01, CHAN = 23
    print("Send message: {}", ResponseStatusCode.get_description(code))
    time.sleep(1)
