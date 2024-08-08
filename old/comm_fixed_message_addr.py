from lib.lora_e220 import LoRaE220, print_configuration, Configuration
from Pin import Pin
from auxController import AuxController
import serial
import time
import json
from lora_e220_operation_constant import ResponseStatusCode, ModeType
import hashlib
from datetime import datetime

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
    addrh = int(address[:2], 16)
    addrl = int(address[2:], 16)
    return addrh, addrl

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

# Initialize LoRa module
lora = LoRaE220('900T22D', aux_pin=aux_controller, m0_pin=m0_pin, m1_pin=m1_pin)
lora.set_mode(ModeType.MODE_0_NORMAL)
time.sleep(1)

code = lora.begin()
print("Begin code:", code)
print(f"Initialization: {ResponseStatusCode.get_description(code)}")

print("Custom configuration..")
custom_conf = Configuration(lora.model)
custom_conf.set_custom_conf(addh=addrh, addl=addrl, CHAN=25)  # Ensure this channel matches the receiver
code_custom, configuration_custom = lora.set_configuration(custom_conf)
print("Custom configuration code:", code_custom)
print_configuration(configuration_custom)

code, configuration = lora.get_configuration()
print("Retrieve configuration code:", code)
print_configuration(configuration)

# Define unique IDs and their respective slots
unique_ids = {
    "492e39d7": 0,
    "403a39d7": 1,
    "3f2e39d7": 2,
    "0a3039d7": 3
}

# Get the time slot for this device
time_slot = unique_ids.get(unique_id, -1)

if time_slot == -1:
    print("Unknown device ID.")
else:
    while True:
        current_time = datetime.utcnow()
        current_slot = (current_time.second // 10) % 4

        if current_slot == time_slot:
            data = unique_id_json_content
            json_data = json.dumps(data)
            print(f"Device {unique_id} sending data at time slot {time_slot}: {json_data}")
            code = lora.send_fixed_message(addrh, addrl, 25, json_data)
            print("Send message code:", code)
            print("Send message description:", ResponseStatusCode.get_description(code))
        
        # Wait for the next slot
        time.sleep(2)
