import hashlib
import json

def generate_address_in_range(unique_id, min_value=1, max_value=81):
    try:
        # Hash the unique ID using SHA-256
        hash_object = hashlib.sha256(unique_id.encode())
        # Convert the hash to an integer
        hash_int = int(hash_object.hexdigest(), 16)
        # Map the hash value to the range min_value to max_value
        address = min_value + (hash_int % (max_value - min_value + 1))
        return address
    except Exception as e:
        print(f"Error generating address: {e}")
        return None

unique_id_path = '/tmp/meta_files/UNIQUE_ID/id-displayboard.json'
with open(unique_id_path, 'r') as file:
    unique_id_json_content = file.read()
    unique_id_data = json.loads(unique_id_json_content)

# Example usage
unique_id = unique_id_data['val']
address = generate_address_in_range(unique_id)
print(f"Generated Address for {unique_id}: {address}")