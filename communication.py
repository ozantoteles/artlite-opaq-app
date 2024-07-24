from lib.lora_e220 import LoRaE220, print_configuration, Configuration
from Pin import Pin
from auxController import AuxController
import serial
import time
import json
from lora_e220_operation_constant import ResponseStatusCode, ModeType
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
lora.set_mode(ModeType.MODE_0_NORMAL)
time.sleep(1)

code = lora.begin()
print(code)
print(f"Initialization: {ResponseStatusCode.get_description(code)}")

print("Custom configuration..")
custom_conf = Configuration(lora.model)
custom_conf.set_custom_conf(addh=addrh, addl=addrl, CHAN=25)
code_custom, configuration_custom = lora.set_configuration(custom_conf)
print("Custom configuration done!")
print_configuration(configuration_custom)

code, configuration = lora.get_configuration()
print("Retrieve configuration: {}", ResponseStatusCode.get_description(code))
print_configuration(configuration)

while True:
    data = unique_id_json_content
    json_data = json.dumps(data)
    print("Length of data being sent:", len(json_data + ','))  # Log the length of serialized JSON data
    code = lora.send_transparent_message(json_data)  # Ensure this method sends the serialized JSON data correctly
    print("Send message:", ResponseStatusCode.get_description(code))
    time.sleep(5)
