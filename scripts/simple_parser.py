def parse_lora_data(data):
    # Remove the initial 'cbda7b' and the trailing '7dbc'
    hex_string = data[6:-4]

    # Decode the hex string into a UTF-8 string
    decoded_string = bytes.fromhex(hex_string).decode('utf-8')

    # Split the string into individual key-value pairs
    key_value_pairs = decoded_string.split(", ")

    # Initialize the dictionary to store the parsed data
    parsed_data = {}

    for pair in key_value_pairs:
        # Split the key and value
        key, value = pair.split(": ")
        
        # Convert value to appropriate data type
        if '.' in value:
            try:
                parsed_value = float(value)
            except ValueError:
                parsed_value = value  # fallback to string if conversion fails
        else:
            try:
                parsed_value = int(value)
            except ValueError:
                parsed_value = value  # fallback to string if conversion fails

        # Add to the dictionary
        parsed_data[key] = parsed_value

    return parsed_data

# Example usage
received_data = "cbda7b22434149525248544c4556454c5f45585445524e414c5f54454d50223a2032372e3035363135333230303537393834332c2022434149525248544c4556454c5f45585445524e414c5f48554d223a2034352e32343931303335333234363335372c20224341495254564f434c4556454c223a2036302c2022434149524e4f324c4556454c223a20312c202243414952504d323030385f312e305f5453495f4c4556454c223a2031332c202243414952504d323030385f322e355f5453495f4c4556454c223a2031332c202243414952504d323030385f31305f5453495f4c4556454c223a2031332c202243414952504d323030385f302e335f4c5f4c4556454c223a20333131342c202243414952504d323030385f302e355f4c5f4c4556454c223a203632312c202243414952504d323030385f312e305f4752494d4d5f4c4556454c223a2031332c202243414952504d323030385f312e305f4c5f4c4556454c223a203132342c202243414952504d323030385f322e355f4752494d4d5f4c4556454c223a2031332c202243414952504d323030385f322e355f4c5f4c4556454c223a2036322c202243414952504d323030385f355f4c5f4c4556454c223a20352c202243414952504d323030385f31305f4752494d4d5f4c4556454c223a2031332c202243414952504d323030385f31305f4c5f4c4556454c223a20302c202243414952434f4c4556454c223a202d3939392c202243414952434f324c4556454c223a203438322c20225354545f424154544552595f4c4556454c223a202d3939392c20225354545f434149525f424154544552595f535441545553223a20307dbc"
parsed_data = parse_lora_data(received_data)

print(parsed_data)
