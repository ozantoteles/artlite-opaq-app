import hashlib
import json
import os
import re
import subprocess

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
    addrh = address[:2]
    addrl = address[2:]
    return addrh, addrl

def get_mac_address(interface):
    try:
        # Use ip command to get the MAC address
        result = subprocess.run(['ip', 'link', 'show', interface], stdout=subprocess.PIPE, text=True)
        # Use regex to extract the MAC address
        mac_address = re.search(r'(?<=ether\s)([0-9a-f:]{17})', result.stdout, re.IGNORECASE).group(0)
        return mac_address.upper()
    except Exception as e:
        print(f"Error getting MAC address: {e}")
        return None

def update_device_config(unique_id, mac_address, json_file_path):
    # Read the existing JSON file
    if os.path.exists(json_file_path):
        with open(json_file_path, 'r') as file:
            data = json.load(file)
    else:
        data = {}

    # Generate the address
    address = generate_address(unique_id)

    # Update the JSON file if the MAC address is not already present
    if mac_address not in [device["macAddr"] for device in data.values()]:
        # Add new device entry
        data[unique_id] = {
            "macAddr": mac_address,
            "ebyteType": "e220",
            "devType": "sender",
            "channel": "0x17",
            "uniqueAddr": f"0x{address}",
            "customAddr": f"0x{address}",
            "reg0": "0x62",
            "reg1": "0x00",
            "reg2": "0x17",
            "reg3": "0x00",
            "cryptH": "0x00",
            "cryptL": "0x00"
        }

        # Write the updated JSON back to the file
        with open(json_file_path, 'w') as file:
            json.dump(data, file, indent=4)

        print(f"Updated device configuration with MAC: {mac_address}")
    else:
        print(f"MAC address {mac_address} is already in the configuration.")

# Path to the unique ID JSON file
unique_id_json_file_path = '/tmp/meta_files/UNIQUE_ID/id-displayboard.json'
# Path to the device configuration JSON file
device_config_json_file_path = '/usr/local/artlite-opaq-app/config/device_config.json'

# Read the unique ID from the JSON file
with open(unique_id_json_file_path, 'r') as file:
    unique_id_data = json.load(file)

# Extract the unique ID
unique_id = unique_id_data['val']

# Get the MAC address of wlan0
mac_address = get_mac_address('wlan0')

if mac_address:
    # Update the device configuration JSON file
    update_device_config(unique_id, mac_address, device_config_json_file_path)
else:
    print("Unable to get MAC address of wlan0.")
