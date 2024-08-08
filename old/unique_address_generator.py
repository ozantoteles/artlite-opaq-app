import hashlib
import json

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

# Path to the JSON file
json_file_path = '/tmp/meta_files/UNIQUE_ID/id-displayboard.json'

# Read the JSON file
with open(json_file_path, 'r') as file:
    data = json.load(file)

# Extract the unique ID
unique_id = data['val']

# Generate the address
address = generate_address(unique_id)

# Split the address into high byte and low byte
addrh, addrl = split_address(address)

print(f"Unique ID: {unique_id}")
print(f"Generated Address: {address}")
print(f"High Byte (addrh): {addrh}")
print(f"Low Byte (addrl): {addrl}")
