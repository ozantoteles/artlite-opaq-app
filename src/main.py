import random
import serial
import time
import json
#from sensorUtils import SensorHandler
#from functionAQI import getQuality

def setup_pins(status):
    print("Setting up pins...")
    # USB2
    # Set USB2
    try:
        with open('/sys/class/leds/usb2_en/brightness', 'w') as f:
            if status == "ON":
                f.write("1")
            else:
                f.write("0")
    except IOError as e:
        print(f"Failed to set USB2: {e}")
    time.sleep(5)
    # Verify USB2
    try:
        with open('/sys/class/leds/usb2_en/brightness', 'r') as f:
            usb2_status = f.read().strip()
            expected_usb2_status = "1" if status == "ON" else "0"
            if usb2_status == expected_usb2_status:
                print(f"USB2 is correctly set to {status}")
            else:
                print(f"USB2 setup failed!")
    except IOError as e:
        print(f"Failed to read USB2: {e}")

    #LORA VCC
    # Set LoRa VCC
    try:
        with open('/sys/class/leds/lazer_cntrl/brightness', 'w') as f:
            if status == "ON":
                f.write("4095")
            else:
                f.write("0")
    except IOError as e:
        print(f"Failed to set LoRa VCC: {e}")
    time.sleep(1)
    # Verify LoRa VCC
    try:
        with open('/sys/class/leds/lazer_cntrl/brightness', 'r') as f:
            lora_status = f.read().strip()
            expected_lora_status = "4095" if status == "ON" else "0"
            if lora_status == expected_lora_status:
                print(f"LoRa VCC is correctly set to {status}")
            else:
                print(f"LoRa VCC setup failed!")
    except IOError as e:
        print(f"Failed to read LoRa VCC: {e}")



def set_mode(mode):
    if mode == "configuration":
        print("Entering into configuration mode..")
        # M0
        # Set configuration mode m0
        try:
            with open('/sys/class/leds/red_cntrl/brightness', 'w') as f:
                f.write("255")
        except IOError as e:
            print(f"Failed to set m0 (red_cntrl): {e}")
        # Verify configuration mode m0
        try:
            with open('/sys/class/leds/red_cntrl/brightness', 'r') as f:
                m0_status = f.read().strip()
                expected_m0_status = "255" 
                if m0_status == expected_m0_status:
                    print(f"m0 is correctly set to 255")
                else:
                    print(f"m0 setup failed!")
        except IOError as e:
            print(f"Failed to read m0: {e}")
            
        # M1
        # Set configuration mode m1
        try:
            with open('/sys/class/leds/green_cntrl/brightness', 'w') as f:
                f.write("255")
        except IOError as e:
            print(f"Failed to set m1 (green_cntrl): {e}")
        # Verify configuration mode m1
        try:
            with open('/sys/class/leds/green_cntrl/brightness', 'r') as f:
                m0_status = f.read().strip()
                expected_m0_status = "255" 
                if m0_status == expected_m0_status:
                    print(f"m1 is correctly set to 255")
                else:
                    print(f"m1 setup failed!")
        except IOError as e:
            print(f"Failed to read m1: {e}")

    elif mode == "normal":
        print("Entering into normal mode..")
        # M0
        # Set configuration mode m0
        try:
            with open('/sys/class/leds/red_cntrl/brightness', 'w') as f:
                f.write("0")
        except IOError as e:
            print(f"Failed to set m0 (red_cntrl): {e}")
        # Verify configuration mode m0
        try:
            with open('/sys/class/leds/red_cntrl/brightness', 'r') as f:
                m0_status = f.read().strip()
                expected_m0_status = "0" 
                if m0_status == expected_m0_status:
                    print(f"m0 is correctly set to 0")
                else:
                    print(f"m0 setup failed!")
        except IOError as e:
            print(f"Failed to read m0: {e}")
            
        # M1
        # Set configuration mode m1
        try:
            with open('/sys/class/leds/green_cntrl/brightness', 'w') as f:
                f.write("0")
        except IOError as e:
            print(f"Failed to set m1 (green_cntrl): {e}")
        # Verify configuration mode m1
        try:
            with open('/sys/class/leds/green_cntrl/brightness', 'r') as f:
                m0_status = f.read().strip()
                expected_m0_status = "0" 
                if m0_status == expected_m0_status:
                    print(f"m1 is correctly set to 0")
                else:
                    print(f"m1 setup failed!")
        except IOError as e:
            print(f"Failed to read m1: {e}")
    
    time.sleep(1)


def get_device_id():
    with open('/tmp/meta_files/UNIQUE_ID/id-displayboard.json') as f:
        data = json.load(f)
        return data['val']

def read_response(ser):
    try:
        print(f"Listening on {ser} at 9600 baud rate...")
        buffer = bytearray()
        while True:
            print("************* ",ser.in_waiting)
            if ser.in_waiting > 0:
                data = ser.read(ser.in_waiting)
                buffer.extend(data)
                
                # Process complete messages
                while True:
                    start_index = buffer.find(b'\xc1')  # Example start delimiter

                    if start_index != -1:
                        complete_message = buffer[start_index:]
                        hex_data = complete_message.hex()
                        print(f"Received Data: {hex_data}")
                        # Remove processed message from buffer
                        #buffer = buffer[end_index + 1:]
                        return hex_data
                    else:
                        break
    except serial.SerialException as e:
        print(f"Error: {e}")
    except KeyboardInterrupt:
        print("Stopped listening.")
    '''
    response = b''
    while len(response) < expected_response_length:
        part = serial_port.read(expected_response_length - len(response))
        if not part:
            break
        response += part
    return response
    '''

def send_configuration_command(serial_port, command, expected_response):
    success = False
    while not success:
        print(f"Sending command: {command.hex()}")
        serial_port.write(command)
        time.sleep(0.1)
        response = read_response(serial_port)
        print(f"Received response: {response}")
        if response == expected_response.hex():
            print(f"Received expected response: {response}")
            success = True
        else:
            print(f"Unexpected response: {response}, retrying...")

def configure_lora(serial_port, ADDH, ADDL, channel):
    print(f"Configuring LoRa module with address: {(ADDH, ADDL)} and channel: {channel}")

    # Set to program mode
    set_mode("configuration")

    # Set address
    address_command = bytes([0xC0, 0x00, 0x03, ADDH, ADDL, 0x62])
    expected_address_response = bytes([0xC1, 0x00, 0x03, ADDH, ADDL, 0x62])
    send_configuration_command(serial_port, address_command, expected_address_response)

    # Set channel
    channel_command = bytes([0xC0, 0x04, 0x01, channel])
    expected_channel_response = bytes([0xC1, 0x04, 0x01, channel])
    send_configuration_command(serial_port, channel_command, expected_channel_response)
    
    # Set to transparent transmission mode
    #transparent_mode_command = bytes([0xC0, 0x05, 0x01, 0x00])
    #expected_transparent_mode_response = bytes([0xC1, 0x05, 0x01, 0x00])
    #send_configuration_command(serial_port, transparent_mode_command, expected_transparent_mode_response)

    # Set devices to normal mode
    #normal_mode_command = bytes([0xC0, 0x05, 0x01, 0x00])
    #expected_normal_mode_response = bytes([0xC1, 0x05, 0x01, 0x00])
    #send_configuration_command(serial_port, normal_mode_command, expected_normal_mode_response)

    time.sleep(2)
    set_mode("normal")



def send_data(ser, device_id):
    try:
        # Define the start and end delimiters
        start_delimiter = b'\x00\x00'
        end_delimiter = b'\x44'
        
        # Example data to send
        # Generate random data payload (e.g., 3 bytes)
        #data_payload = bytes([random.randint(0, 255) for _ in range(3)])
        data_payload = device_id.encode('utf-8')
        # Create the full message
        full_message = start_delimiter + data_payload + end_delimiter
        
        # Send the message
        #while True:
        ser.write(full_message)
        print(f"Sent Data: {full_message.hex()}")
        time.sleep(1)  # Send data every second for testing purposes
    except serial.SerialException as e:
        print(f"Error: {e}")
    except KeyboardInterrupt:
        print("Stopped sending.")


'''
def read_sensor():
    __sensor = SensorHandler()

    sensor_data = __sensor.handler()

    dataTemp = sensor_data["CAIRRHTLEVEL_EXTERNAL_TEMP"]
    dataHum = sensor_data["CAIRRHTLEVEL_EXTERNAL_HUM"]
    dataCO2 = sensor_data["CAIRCO2LEVEL"]
    dataVOC = sensor_data["CAIRTVOCLEVEL"]
    dataNO2 = sensor_data["CAIRNO2LEVEL"]
    dataPM1_0 = sensor_data["CAIRPM2008_1.0_TSI_LEVEL"]
    dataPM2_5 = sensor_data["CAIRPM2008_2.5_TSI_LEVEL"]
    dataPM10 = sensor_data["CAIRPM2008_10_TSI_LEVEL"]

    
    sttCairHealthLevel, sttCairHealthStatus = getQuality("AQI.json",dataNO2,dataVOC,dataPM10,dataPM1_0,dataCO2,dataPM2_5)
    
    serial_message = (
        "*" +
        str(int(dataTemp)) + ";" +
        str(int(dataHum)) + ";" +
        str(dataCO2) + ";" +
        str(dataVOC) + ";" +
        str(dataNO2) + ";" +
        str(dataPM1_0) + ";" +
        str(dataPM2_5) + ";" +
        str(dataPM10) + ";" +
        str(int(sttCairHealthLevel)) + "*"
    )

    return serial_message
'''

if __name__ == "__main__":

    setup_pins("OFF")
    setup_pins("ON")
    set_mode("configuration")
    set_mode("normal")

    try:
        with open("/usr/local/artlite-opaq-app/config/device_config.json", 'r') as f:
            unique_ids = json.load(f)
    except IOError as e:
        print(f"Failed to read device configuration: {e}")

    device_id = get_device_id()

    if device_id in unique_ids:
        while True:
            uniqueAddr_str = unique_ids[device_id]["uniqueAddr"] 
            channel_str = unique_ids[device_id]["channel"] 

            # Convert the strings to hexadecimal integers
            channel = int(channel_str, 16)
            unique_addr_hex = int(uniqueAddr_str, 16)

            # Parse uniqueAddr hex into low and high bytes
            ADDL = unique_addr_hex & 0xFF  # Extract the low byte
            ADDH = (unique_addr_hex >> 8) & 0xFF  # Extract the high byte

            # Print the results
            print(f"Channel Hex: {channel:#x}")
            print(f"UniqueAddr Hex: {unique_addr_hex:#x}")
            print(f"UniqueAddr Low Byte: {ADDL:#x}")
            print(f"UniqueAddr High Byte: {ADDH:#x}")

            with serial.Serial('/dev/ttyUSB0', 9600, timeout=1) as ser:
                configure_lora(ser, ADDH, ADDL, channel)

                # Flush any stale data in the buffers
                ser.flushInput()
                ser.flushOutput()

                time.sleep(1)

                send_data(ser, device_id)

                time.sleep(5)


