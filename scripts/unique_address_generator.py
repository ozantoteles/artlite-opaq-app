import argparse
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

def update_device_config(unique_id, mac_address, json_file_path, args):
    # Generate the address
    address = generate_address(unique_id)

    # Use custom address if provided, else set it to the same as uniqueAddr
    custom_address = args.customAddr if args.customAddr else f"0x{address}"

    # Update default values with provided arguments
    defaults = {
        "ebyteType": args.ebyteType if args.ebyteType else "e220",
        "devType": args.devType if args.devType else "sender",
        "channel": args.channel if args.channel else "0x17",
        "reg0": args.reg0 if args.reg0 else "0x62",
        "reg1": args.reg1 if args.reg1 else "0x00",
        "reg2": args.reg2 if args.reg2 else "0x17",
        "reg3": args.reg3 if args.reg3 else "0x00",
        "cryptH": args.cryptH if args.cryptH else "0x00",
        "cryptL": args.cryptL if args.cryptL else "0x00"
    }

    # Read the existing JSON file
    if os.path.exists(json_file_path):
        with open(json_file_path, 'r') as file:
            data = json.load(file)
    else:
        data = {}

    # Check if the MAC address is already in the configuration
    device_entry = next((key for key, value in data.items() if value.get("macAddr") == mac_address), None)

    if device_entry:
        # If the MAC address already exists, update the device's configuration
        print(f"MAC address {mac_address} is already in the configuration. Updating its values.")
        data[device_entry].update({
            "uniqueAddr": f"0x{address}",
            "customAddr": custom_address,  # If not provided, this is the same as uniqueAddr
            **defaults
        })
    else:
        # Add a new device entry
        print(f"Adding a new device entry for MAC address {mac_address}.")
        data[unique_id] = {
            "macAddr": mac_address,
            "uniqueAddr": f"0x{address}",
            "customAddr": custom_address,  # If not provided, this is the same as uniqueAddr
            **defaults
        }

    # Write the updated JSON back to the file, overwriting if it exists
    with open(json_file_path, 'w') as file:
        json.dump(data, file, indent=4)

    print(f"Updated device configuration with MAC: {mac_address}")




def main(args):
    # Path to the unique ID JSON file
    unique_id_json_file_path = args.unique_id_json_file_path
    # Path to the device configuration JSON file
    device_config_json_file_path = args.device_config_json_file_path

    # Read the unique ID from the JSON file
    with open(unique_id_json_file_path, 'r') as file:
        unique_id_data = json.load(file)

    # Extract the unique ID
    unique_id = unique_id_data['val']

    # Get the MAC address of the specified interface
    mac_address = get_mac_address(args.interface)

    if mac_address:
        # Update the device configuration JSON file
        update_device_config(unique_id, mac_address, device_config_json_file_path, args)
    else:
        print(f"Unable to get MAC address of {args.interface}.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Update device configuration JSON file.')
    parser.add_argument('interface', type=str, help='Network interface to get MAC address from')
    parser.add_argument('--unique_id_json', dest='unique_id_json_file_path', type=str, default='/tmp/meta_files/UNIQUE_ID/id-displayboard.json', help='Path to unique ID JSON file')
    parser.add_argument('--device_config_json', dest='device_config_json_file_path', type=str, default='/usr/local/artlite-opaq-app/config/device_config.json', help='Path to device configuration JSON file')
    parser.add_argument('--ebyteType', type=str, help='Type of ebyte')
    parser.add_argument('--devType', type=str, help='Type of device')
    parser.add_argument('--channel', type=str, help='Channel information')
    parser.add_argument('--reg0', type=str, help='Register 0 value')
    parser.add_argument('--reg1', type=str, help='Register 1 value')
    parser.add_argument('--reg2', type=str, help='Register 2 value')
    parser.add_argument('--reg3', type=str, help='Register 3 value')
    parser.add_argument('--cryptH', type=str, help='Crypt H value')
    parser.add_argument('--cryptL', type=str, help='Crypt L value')
    parser.add_argument('--customAddr', type=str, help='Custom address for the device')  # Add customAddr argument

    args = parser.parse_args()
    main(args)

