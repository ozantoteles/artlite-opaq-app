import serial
import time
import json
import os

# Configuration parameters
unique_ids = {
    "492e39d7": {"address": (0x01, 0x00), "channel": 17},  # Sender 1
    "403a39d7": {"address": (0x01, 0x01), "channel": 18},  # Sender 2
    "270b81d7": {"address": (0x01, 0x02), "channel": 19},  # Sender 3
    "0a3039d7": {"address": (0x01, 0x03), "channel": 20},  # Sender 4
    "3f2e39d7": "receiver"  # Receiver 
}

def get_device_id():
    with open('/tmp/meta_files/UNIQUE_ID/id-displayboard.json') as f:
        data = json.load(f)
        return data['val']

def read_response(serial_port, expected_response_length):
    response = b''
    while len(response) < expected_response_length:
        part = serial_port.read(expected_response_length - len(response))
        if not part:
            break
        response += part
    return response

def set_mode(mode):
    if mode == "program":
        os.system('echo 255 > /sys/class/leds/red_cntrl/brightness')
        os.system('echo 255 > /sys/class/leds/green_cntrl/brightness')
    elif mode == "normal":
        os.system('echo 0 > /sys/class/leds/red_cntrl/brightness')
        os.system('echo 0 > /sys/class/leds/green_cntrl/brightness')
    time.sleep(1)

def send_configuration_command(serial_port, command, expected_response):
    success = False
    while not success:
        print(f"Sending command: {command.hex()}")
        serial_port.write(command)
        time.sleep(0.1)
        response = read_response(serial_port, len(expected_response))
        print(f"Received response: {response.hex()}")
        if response == expected_response:
            print(f"Received expected response: {response.hex()}")
            success = True
        else:
            print(f"Unexpected response: {response.hex()}, retrying...")

def configure_lora(serial_port, address, channel):
    print(f"Configuring LoRa module with address: {address} and channel: {channel}")

    # Set to program mode
    set_mode("program")

    # Set address
    ADDH, ADDL = address
    address_command = bytes([0xC0, 0x00, 0x03, ADDH, ADDL, 0x62])
    expected_address_response = bytes([0xC1, 0x00, 0x03, ADDH, ADDL, 0x62])
    send_configuration_command(serial_port, address_command, expected_address_response)

    # Set channel
    channel_command = bytes([0xC0, 0x04, 0x01, channel])
    expected_channel_response = bytes([0xC1, 0x04, 0x01, channel])
    send_configuration_command(serial_port, channel_command, expected_channel_response)

    # Set devices to normal mode
    normal_mode_command = bytes([0xC0, 0x05, 0x01, 0x00])
    expected_normal_mode_response = bytes([0xC1, 0x05, 0x01, 0x00])
    send_configuration_command(serial_port, normal_mode_command, expected_normal_mode_response)

def setup_pins():
    print("Setting up pins...")
    os.system('echo 1 > /sys/class/leds/usb2_en/brightness')
    time.sleep(5)
    print("USB2 enabled")
    os.system('echo 4096 > /sys/class/leds/lazer_cntrl/brightness')
    print("LoRa VCC enabled")

def reset_pins():
    print("Resetting pins...")
    os.system('echo 0 > /sys/class/leds/red_cntrl/brightness')
    print("LoRa M0 disabled")
    os.system('echo 0 > /sys/class/leds/green_cntrl/brightness')
    print("LoRa M1 disabled")

def send_data(device_id, address, channel):
    print(f"Device ID: {device_id} configured as sender with address {address} on channel {channel}")

    setup_pins()
    
    with serial.Serial('/dev/ttyUSB0', 9600, timeout=1) as ser:
        configure_lora(ser, address, channel)
        
        while True:
            data = f"Data from {device_id}"
            print(f"Sending data: {data}")
            ser.write(data.encode())
            time.sleep(5)  # Send data every 5 seconds

    reset_pins()

def receive_data():
    device_id = get_device_id()
    print(f"Device ID: {device_id} configured as receiver")
    
    setup_pins()

    with serial.Serial('/dev/ttyUSB0', 9600, timeout=1) as ser:
        while True:
            for id_info in unique_ids.values():
                if isinstance(id_info, dict):
                    address = id_info["address"]
                    channel = id_info["channel"]
                    configure_lora(ser, address, channel)
                    print(f"Listening on channel: {channel}")
                    start_time = time.time()
                    while time.time() - start_time < 30:  # Listen on each channel for 30 seconds
                        data = ser.read(100)
                        if data:
                            try:
                                decoded_data = data.decode()
                                print(f"Received: {decoded_data} on channel {channel}")
                            except UnicodeDecodeError:
                                print(f"Received non-decodable data: {data.hex()} on channel {channel}")
                        else:
                            print(f"No data received on channel {channel}")
                    time.sleep(1)

    reset_pins()

if __name__ == "__main__":
    device_id = get_device_id()
    if device_id in unique_ids:
        if unique_ids[device_id] == "receiver":
            receive_data()
        else:
            send_data(device_id, unique_ids[device_id]["address"], unique_ids[device_id]["channel"])
    else:
        print("Device ID not configured.")
