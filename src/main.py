# src/main.py

# Standard Library Imports
import os
import sys
import time
import json
import random
import logging
from logging.handlers import RotatingFileHandler
import threading
from datetime import datetime
from collections import deque

# Third-Party Imports
import serial
import pyudev
import asyncio
import serial_asyncio  # Requires pyserial-asyncio package
from pymodbus.datastore import ModbusSlaveContext, ModbusServerContext, ModbusSequentialDataBlock
from pymodbus.server.async_io import StartAsyncSerialServer
from pymodbus.transaction import ModbusRtuFramer
from pymodbus.device import ModbusDeviceIdentification

# Local/Application-Specific Imports
sys.path.append(os.path.abspath('/usr/local/artlite-opaq-app'))
from sensorUtils import SensorHandler
from functionAQI import getQuality
from arduino_iot_cloud import ArduinoCloudClient, Task # pip3.10 install arduino_iot_cloud, Successfully installed arduino_iot_cloud-1.4.0 cbor2-5.6.5 micropython-senml-0.1.1


# Configure logging
logging.basicConfig(level=logging.DEBUG,  # Set the logging level
                    format='%(asctime)s - %(levelname)s - %(pathname)s - %(lineno)d - %(funcName)s - %(message)s',
                    # Include file name and function name
                    datefmt='%Y-%m-%d %H:%M:%S',  # Date format
                    handlers=[
                        logging.StreamHandler(),  # Log to console
                        RotatingFileHandler("app.log", maxBytes=1024 * 1024, backupCount=3)
                        # Log to a file with rotation
                    ])

device_mapping_path = "/usr/local/artlite-opaq-app/config/device_mapping.json"
modbus_array = None
cloud_array = []  # First initialization
cloud_array_lock = threading.Lock()
client = None
modbus_device = None
lora_device = None

# Time intervals
MONITOR_INTERVAL = 10 * 60  # 10 minutes in seconds

# Store last update times
last_update_times = {}

def get_value_callback(index):
    def callback(client, value_name=None):
        with cloud_array_lock:
            if index < len(cloud_array):
                return cloud_array[index]
            else:
                return None  # Return a default value or None if the index is out of range

    return callback


def cloud_tasks():
    logging.info("Starting Arduino Cloud Functionality")
    global client

    with open('/usr/local/artlite-opaq-app/config/secrets.json', 'r') as file:
        secrets = json.load(file)
        DEVICE_ID = secrets['DEVICE_ID']
        SECRET_KEY = secrets['SECRET_KEY']

    # Set sync_mode=True for synchronous operation
    client = ArduinoCloudClient(device_id=DEVICE_ID, username=DEVICE_ID, password=SECRET_KEY, sync_mode=True)

    # Determine the number of devices based on cloud_array size
    num_devices = len(cloud_array) // 10
    logging.info(f"Configuring cloud tasks for {num_devices} devices.")

    # Register each value with an on_read callback and set an interval
    interval = 20.0  # Adjust as needed
    for i in range(1, num_devices + 1):
        start_index = (i - 1) * 10
        client.register(f'dev_id_{i}', value=0, on_read=get_value_callback(start_index), interval=interval)
        client.register(f'temperature_{i}', value=0, on_read=get_value_callback(start_index + 1), interval=interval)
        client.register(f'humidity_{i}', value=0, on_read=get_value_callback(start_index + 2), interval=interval)
        client.register(f'pm1_0_{i}', value=0, on_read=get_value_callback(start_index + 3), interval=interval)
        client.register(f'pm2_5_{i}', value=0, on_read=get_value_callback(start_index + 4), interval=interval)
        client.register(f'pm10_{i}', value=0, on_read=get_value_callback(start_index + 5), interval=interval)
        client.register(f'co2_{i}', value=0, on_read=get_value_callback(start_index + 6), interval=interval)
        client.register(f'voc_index_{i}', value=0, on_read=get_value_callback(start_index + 7), interval=interval)
        client.register(f'nox_index_{i}', value=0, on_read=get_value_callback(start_index + 8), interval=interval)
        client.register(f'air_quality_index_{i}', value=0, on_read=get_value_callback(start_index + 9), interval=interval)

    client.start()

    # Add a loop to periodically call client.update()
    while True:
        try:
            client.update()
        except Exception as e:
            logging.error(f"Error during client update: {e}")
        time.sleep(0.1)  # Adjust the sleep time as needed


def get_ttyUSB_device(module_name):
    # Define a mapping for USB paths to module names
    module_mapping = {
        'usb2/2-1': 'FTDI Module Connected to Lora Module',
        'usb1/1-1': 'FTDI Module Connected to MODBUS Module',
    }

    # Reverse the mapping to lookup by module name
    name_to_path = {v: k for k, v in module_mapping.items()}

    # Check if the provided module name exists in the mapping
    if module_name not in name_to_path:
        raise ValueError(f"Module name '{module_name}' not found in mapping.")

    target_path = name_to_path[module_name]

    context = pyudev.Context()

    # Iterate through all ttyUSB devices
    for device in context.list_devices(subsystem='tty', ID_BUS='usb'):
        # Get the parent device, which corresponds to the USB device
        parent = device.find_parent(subsystem='usb')

        if parent is not None:
            # Extract only the usbX/X-Y part of the device path for mapping
            usb_path_parts = parent.device_path.split('/')
            usb_path = '/'.join(usb_path_parts[-3:-1])

            # Check if this USB path matches the target path
            if usb_path == target_path:
                return device.device_node

    # Return None if no matching device is found
    return None


def setup_pins(status):
    logging.debug("Setting up pins...")
    # USB2
    # Set USB2
    try:
        with open('/sys/class/leds/usb2_en/brightness', 'w') as f:
            if status == "ON":
                f.write("1")
            else:
                f.write("0")
    except IOError as e:
        logging.debug(f"Failed to set USB2: {e}")
    time.sleep(5)
    # Verify USB2
    try:
        with open('/sys/class/leds/usb2_en/brightness', 'r') as f:
            usb2_status = f.read().strip()
            expected_usb2_status = "1" if status == "ON" else "0"
            if usb2_status == expected_usb2_status:
                logging.debug(f"USB2 is correctly set to {status}")
            else:
                logging.debug(f"USB2 setup failed!")
    except IOError as e:
        logging.debug(f"Failed to read USB2: {e}")

    #LORA VCC
    # Set LoRa VCC
    try:
        with open('/sys/class/leds/lazer_cntrl/brightness', 'w') as f:
            if status == "ON":
                f.write("4095")
            else:
                f.write("0")
    except IOError as e:
        logging.debug(f"Failed to set LoRa VCC: {e}")
    time.sleep(1)
    # Verify LoRa VCC
    try:
        with open('/sys/class/leds/lazer_cntrl/brightness', 'r') as f:
            lora_status = f.read().strip()
            expected_lora_status = "4095" if status == "ON" else "0"
            if lora_status == expected_lora_status:
                logging.debug(f"LoRa VCC is correctly set to {status}")
            else:
                logging.debug(f"LoRa VCC setup failed!")
    except IOError as e:
        logging.debug(f"Failed to read LoRa VCC: {e}")


def set_mode(ebyte_type, mode):
    if mode == "configuration":
        if ebyte_type == "e220":
            logging.debug("Entering into configuration mode..")
            # M0
            # Set configuration mode m0

            try:
                with open('/sys/class/leds/red_cntrl/brightness', 'w') as f:
                    f.write("255")
            except IOError as e:
                logging.debug(f"Failed to set m0 (red_cntrl): {e}")
            # Verify configuration mode m0
            try:
                with open('/sys/class/leds/red_cntrl/brightness', 'r') as f:
                    m0_status = f.read().strip()
                    expected_m0_status = "255"
                    if m0_status == expected_m0_status:
                        logging.debug(f"m0 is correctly set to 255")
                    else:
                        logging.debug(f"m0 setup failed!")
            except IOError as e:
                logging.debug(f"Failed to read m0: {e}")

            # M1
            # Set configuration mode m1
            try:
                with open('/sys/class/leds/green_cntrl/brightness', 'w') as f:
                    f.write("255")
            except IOError as e:
                logging.debug(f"Failed to set m1 (green_cntrl): {e}")
            # Verify configuration mode m1
            try:
                with open('/sys/class/leds/green_cntrl/brightness', 'r') as f:
                    m0_status = f.read().strip()
                    expected_m0_status = "255"
                    if m0_status == expected_m0_status:
                        logging.debug(f"m1 is correctly set to 255")
                    else:
                        logging.debug(f"m1 setup failed!")
            except IOError as e:
                logging.debug(f"Failed to read m1: {e}")


        elif ebyte_type == "e22":
            logging.debug("Entering into configuration mode..")
            # M0
            # Set configuration mode m0

            try:
                with open('/sys/class/leds/red_cntrl/brightness', 'w') as f:
                    f.write("255")
            except IOError as e:
                logging.debug(f"Failed to set m0 (red_cntrl): {e}")
            # Verify configuration mode m0
            try:
                with open('/sys/class/leds/red_cntrl/brightness', 'r') as f:
                    m0_status = f.read().strip()
                    expected_m0_status = "255"
                    if m0_status == expected_m0_status:
                        logging.debug(f"m0 is correctly set to 255")
                    else:
                        logging.debug(f"m0 setup failed!")
            except IOError as e:
                logging.debug(f"Failed to read m0: {e}")

            # M1
            # Set configuration mode m1
            try:
                with open('/sys/class/leds/green_cntrl/brightness', 'w') as f:
                    f.write("0")
            except IOError as e:
                logging.debug(f"Failed to set m1 (green_cntrl): {e}")
            # Verify configuration mode m1
            try:
                with open('/sys/class/leds/green_cntrl/brightness', 'r') as f:
                    m0_status = f.read().strip()
                    expected_m0_status = "0"
                    if m0_status == expected_m0_status:
                        logging.debug(f"m1 is correctly set to 0")
                    else:
                        logging.debug(f"m1 setup failed!")
            except IOError as e:
                logging.debug(f"Failed to read m1: {e}")

    elif mode == "normal":
        logging.debug("Entering into normal mode..")
        # M0
        # Set normal mode m0
        try:
            with open('/sys/class/leds/red_cntrl/brightness', 'w') as f:
                f.write("0")
        except IOError as e:
            logging.debug(f"Failed to set m0 (red_cntrl): {e}")
        # Verify normal mode m0
        try:
            with open('/sys/class/leds/red_cntrl/brightness', 'r') as f:
                m0_status = f.read().strip()
                expected_m0_status = "0"
                if m0_status == expected_m0_status:
                    logging.debug(f"m0 is correctly set to 0")
                else:
                    logging.debug(f"m0 setup failed!")
        except IOError as e:
            logging.debug(f"Failed to read m0: {e}")

        # M1
        # Set normal mode m1
        try:
            with open('/sys/class/leds/green_cntrl/brightness', 'w') as f:
                f.write("0")
        except IOError as e:
            logging.debug(f"Failed to set m1 (green_cntrl): {e}")
        # Verify normal mode m1
        try:
            with open('/sys/class/leds/green_cntrl/brightness', 'r') as f:
                m0_status = f.read().strip()
                expected_m0_status = "0"
                if m0_status == expected_m0_status:
                    logging.debug(f"m1 is correctly set to 0")
                else:
                    logging.debug(f"m1 setup failed!")
        except IOError as e:
            logging.debug(f"Failed to read m1: {e}")

    time.sleep(1)


def get_device_id():
    with open('/tmp/meta_files/UNIQUE_ID/id-displayboard.json') as f:
        data = json.load(f)
        return data['val']


def read_response(ser, timeout=5):
    try:
        logging.debug(f"Listening on {ser} at 9600 baud rate...")
        buffer = bytearray()
        start_time = time.time()

        while True:
            logging.debug(f"Waiting Serial Data: {ser.in_waiting}")
            if ser.in_waiting > 0:
                data = ser.read(ser.in_waiting)
                buffer.extend(data)
                start_time = time.time()  # Reset the timer when data is received

                # Process complete messages
                while True:
                    start_index = buffer.find(b'\xc1')  # Example start delimiter

                    if start_index != -1:
                        complete_message = buffer[start_index:]
                        hex_data = complete_message.hex()
                        logging.debug(f"Received Data: {hex_data}")
                        return hex_data
                    else:
                        break
            elif time.time() - start_time > timeout:
                raise TimeoutError("No data received within timeout period.")

    except serial.SerialException as e:
        logging.debug(f"Serial error: {e}")
        # You can handle the serial exception here, e.g., by restarting the service
    except TimeoutError as e:
        logging.debug(f"Timeout error: {e}")
        # You can handle the timeout here, e.g., by restarting the service
    except KeyboardInterrupt:
        logging.debug("Stopped listening.")


def send_configuration_command(serial_port, command, expected_response):
    success = False
    retries = 0
    max_retries = 3  # Set the maximum number of retries before applying the fix

    while not success and retries < max_retries:
        logging.debug(f"Sending command: {command.hex()}")
        serial_port.write(command)
        time.sleep(0.1)
        response = read_response(serial_port)
        logging.debug(f"Received response: {response}")

        if response == expected_response.hex():
            logging.debug(f"Received expected response: {response}")
            success = True
        else:
            logging.debug(f"Unexpected response: {response}, retrying...")
            retries += 1

    if not success:
        raise Exception("Failed to receive the expected response after retries.")


def configure_lora(serial_port, ebyte_type, ADDH, ADDL, channel):
    logging.debug(f"Configuring LoRa module with address: {(ADDH, ADDL)} and channel: {channel}")

    # Set to program mode
    set_mode(ebyte_type, "configuration")

    if ebyte_type == "e220":

        # Set address
        address_command = bytes([0xC0, 0x00, 0x03, ADDH, ADDL, 0x62])
        expected_address_response = bytes([0xC1, 0x00, 0x03, ADDH, ADDL, 0x62])
        send_configuration_command(serial_port, address_command, expected_address_response)

        # Set channel
        channel_command = bytes([0xC0, 0x04, 0x01, channel])
        expected_channel_response = bytes([0xC1, 0x04, 0x01, channel])
        send_configuration_command(serial_port, channel_command, expected_channel_response)

    elif ebyte_type == "e22":

        # Set address
        address_command = bytes([0xC0, 0x00, 0x04, ADDH, ADDL, 0x00, 0x62])
        expected_address_response = bytes([0xC1, 0x00, 0x04, ADDH, ADDL, 0x00, 0x62])
        send_configuration_command(serial_port, address_command, expected_address_response)

        # Set channel
        channel_command = bytes([0xC0, 0x05, 0x01, channel])
        expected_channel_response = bytes([0xC1, 0x05, 0x01, channel])
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
    set_mode(ebyte_type, "normal")


def send_data(ser, device_id):
    try:
        # Define the start and end delimiters
        start_delimiter = b'\xcb\xda'
        end_delimiter = b'\xbc\x0a'

        # Example data to send
        # Generate random data payload (e.g., 3 bytes)
        #data_payload = bytes([random.randint(0, 255) for _ in range(3)])
        #data_payload = device_id.encode('utf-8')
        # Create the full message
        #full_message = start_delimiter + data_payload + end_delimiter
        message = device_id + read_sensor()
        # Send the message
        #while True:
        logging.debug(f"Sent Data: {message}")
        json_str = json.dumps(message)

        # Step 3: Encode the JSON string to bytes
        json_bytes = json_str.encode('utf-8')

        # Step 4: Convert the bytes to a hexadecimal string
        hex_data = json_bytes.hex()
        ser.write(start_delimiter + bytes.fromhex(hex_data) + end_delimiter)

        time.sleep(1)  # Send data every second for testing purposes
    except serial.SerialException as e:
        logging.debug(f"Error: {e}")
    except KeyboardInterrupt:
        logging.debug("Stopped sending.")


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

    sttCairHealthLevel, sttCairHealthStatus = getQuality("/usr/local/artlite-opaq-app/data/AQI.json", dataNO2 = dataNO2, dataVOC = dataVOC, dataPM10 = dataPM10, dataPM1_0 = dataPM1_0, dataCO2 = dataCO2, dataPM2_5 = dataPM2_5)

    serial_message = (
            ";" +
            str(int(dataTemp)) + ";" +
            str(int(dataHum)) + ";" +
            str(dataCO2) + ";" +
            str(dataVOC) + ";" +
            str(dataNO2) + ";" +
            str(dataPM1_0) + ";" +
            str(dataPM2_5) + ";" +
            str(dataPM10) + ";" +
            str(int(sttCairHealthLevel))
    )

    return serial_message


def parse_lora_data(data):
    # Ensure we are working only with the hex part of the message
    if data.startswith('cbda') and data.endswith('bc'):
        # Remove the 'cbda' prefix and 'bc' suffix
        hex_string = data[4:-4]  ## -4 dogru mu
    else:
        return {"error": "Invalid message format"}

    try:
        # Decode the hex string into a string of ASCII characters
        decoded_string = bytes.fromhex(hex_string).decode('ascii')
    except ValueError:
        return {"error": "Invalid hex data"}

    # Split the string into individual values by semicolon
    values = decoded_string.split(";")

    # Assuming the format is fixed, assign values to their respective keys
    # The keys below are arbitrary; replace them with appropriate labels as needed
    parsed_data = {
        "UniqueID": values[0],
        "Temperature": values[1],
        "Humidity": values[2],
        "CO2": values[3],
        "VOC": values[4],
        "NOx": values[5],
        "PM1": values[6],
        "PM2_5": values[7],
        "PM10": values[8],
        "AQI": values[9] if len(values) > 9 else None,  # Handle cases with fewer fields
    }

    return parsed_data


def log_with_size_limit(log_file_path, log_entry, max_size_kb=100):
    """
    Appends a log entry with a timestamp to the log file and ensures the file size does not exceed max_size_kb.
    
    :param log_file_path: Path to the log file.
    :param log_entry: The log entry string to append.
    :param max_size_kb: Maximum allowed size of the log file in kilobytes.
    """
    max_size_bytes = max_size_kb * 1024

    # Get the current timestamp and format it
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Prepend the timestamp to the log entry
    log_entry_with_timestamp = f"[{timestamp}] {log_entry}"

    # Append the new log entry with timestamp
    with open(log_file_path, 'a+') as log_file:
        log_file.write(log_entry_with_timestamp + '\n')
        log_file.flush()

    # Check if file size exceeds the limit
    current_size = os.path.getsize(log_file_path)
    logging.debug(f"Log file size after writing: {current_size} bytes (Limit: {max_size_bytes} bytes)")

    if current_size <= max_size_bytes:
        logging.debug("File size is within limit, no truncation needed.")
        return  # Size is within limit, no action needed

    # If file size exceeds the limit, reduce file size by removing oldest lines
    logging.debug("File size exceeded limit. Starting truncation process.")
    with open(log_file_path, 'r+') as log_file:
        lines = deque(log_file)

        lines_removed = 0
        while current_size > max_size_bytes and lines:
            lines.popleft()  # Remove the oldest line
            lines_removed += 1
            log_file.seek(0)
            log_file.writelines(lines)
            log_file.truncate()
            log_file.flush()
            current_size = os.path.getsize(log_file_path)
            logging.debug(f"Log file size after truncation: {current_size} bytes")

        logging.debug(f"Truncation complete. Lines removed: {lines_removed}")


def initialize_modbus_array(device_mapping_path):
    # Load the device mapping from JSON
    with open(device_mapping_path, 'r') as f:
        device_mapping = json.load(f)

    # Initialize the modbus array with zeros for each device
    modbus_array = []
    for device_id in device_mapping.values():
        modbus_array.extend([int(device_id)] + [0] * 9)  # 10 fields: device_id + 9 zeros

    logging.debug(f"Initialized Modbus Array: {modbus_array}")
    return modbus_array


def update_modbus_array(modbus_array, parsed_data, device_mapping_path):
    try:
        global last_update_times
        # Load the device mapping from JSON
        with open(device_mapping_path, 'r') as f:
            device_mapping = json.load(f)

        # Check if 'UniqueID' exists in parsed_data
        if 'UniqueID' not in parsed_data:
            logging.error("Parsed data does not contain 'UniqueID'. Modbus array will not be updated.")
            return modbus_array

        unique_id = parsed_data.get('UniqueID', '').strip('"')  # Remove the extra quotes from UniqueID
        if unique_id in device_mapping:
            device_id = int(device_mapping[unique_id])  # Convert to unsigned integer
            try:
                # Find the index of this device_id in the flat modbus_array
                start_index = find_device_index(device_id)
                if start_index == -1:
                    raise ValueError(f"Device ID {device_id} not found in Modbus Array.")
                
                logging.debug(f"Updating Modbus Array at index {start_index} for Device ID {device_id}")
                logging.debug(f"Modbus Array before update: {modbus_array[start_index:start_index + 10]}")

                # Update the array for this device with actual data as unsigned integers
                modbus_array[start_index:start_index + 10] = [
                    device_id,
                    int(parsed_data.get('Temperature', 0)) & 0xFFFF,
                    int(parsed_data.get('Humidity', 0)) & 0xFFFF,
                    int(parsed_data.get('CO2', 0)) & 0xFFFF,
                    int(parsed_data.get('VOC', 0)) & 0xFFFF,
                    int(parsed_data.get('NOx', 0)) & 0xFFFF,
                    int(parsed_data.get('PM1', 0)) & 0xFFFF,
                    int(parsed_data.get('PM2_5', 0)) & 0xFFFF,
                    int(parsed_data.get('PM10', 0)) & 0xFFFF,
                    int(parsed_data.get('AQI', 0)) & 0xFFFF
                ]
                
                logging.debug(f"Modbus Array after update: {modbus_array[start_index:start_index + 10]}")

                # Update last update time
                last_update_times[device_id] = datetime.now()

            except ValueError as e:
                logging.error(f"Device ID {device_id} not found in Modbus Array. Error: {e}")
        else:
            logging.debug(f"UniqueID {unique_id} not found in device mapping.")

    except Exception as e:
        logging.error(f"Error updating Modbus Array: {e}")

    return modbus_array

def handle_message(message, device_id):
    # Check if the message contains the unique device ID
    if f"{device_id}" in message:
        if "SERVICE_RESTART" in message:
            logging.debug("Service restart command received.")
            os.system("systemctl restart artlite-opaq-app.service")
        elif "REBOOT" in message:
            logging.debug("Reboot command received.")
            os.system("reboot")
        else:
            logging.debug(f"Received other message with ID: {message}")
    else:
        logging.debug(f"Received message without matching ID: {message}")


def find_device_index(device_id):
    """Find the start index of a device in the modbus_array."""
    for i in range(0, len(modbus_array), 10):
        if modbus_array[i] == device_id:
            return i
    return -1

async def monitor_modbus_array():
    global last_update_times
    while True:
        now = datetime.now()
        for device_id in last_update_times.keys():
            last_update_time = last_update_times[device_id]
            if (now - last_update_time).total_seconds() > MONITOR_INTERVAL:
                # Handle outdated data by setting only the last element to FF
                start_index = find_device_index(device_id)
                if start_index != -1:
                    logging.info(f"Device {device_id} not updated for a while. Updating Modbus array.")
                    # Update only the last element of the 10 data points
                    modbus_array[start_index + 9] = 0xFF
        await asyncio.sleep(60)  # Check every minute

def initialize_cloud_array(device_mapping_path):
    # Load the device mapping from JSON
    with open(device_mapping_path, 'r') as f:
        device_mapping = json.load(f)

    # Initialize the cloud array with zeros for each device
    cloud_array = []
    for device_id in device_mapping.values():
        cloud_array.extend([int(device_id)] + [0] * 9)  # 10 fields: device_id + 9 zeros

    logging.debug(f"Initialized Cloud Array: {cloud_array}")
    return cloud_array


def update_cloud_array(cloud_array, parsed_data, device_mapping_path):
    try:
        # Load the device mapping from JSON
        with open(device_mapping_path, 'r') as f:
            device_mapping = json.load(f)

        # Check if 'UniqueID' exists in parsed_data
        if 'UniqueID' not in parsed_data:
            logging.error("Parsed data does not contain 'UniqueID'. Cloud array will not be updated.")
            return cloud_array

        unique_id = parsed_data['UniqueID'].strip('"')  # Remove the extra quotes from UniqueID
        if unique_id in device_mapping:
            device_id = int(device_mapping[unique_id])  # Convert to unsigned integer
            try:
                # Find the index of this device_id in the flat cloud_array
                start_index = -1
                for i in range(0, len(cloud_array), 10):
                    if cloud_array[i] == device_id:
                        start_index = i
                        break

                if start_index == -1:
                    raise ValueError(f"Device ID {device_id} not found in Cloud Array.")

                logging.debug(f"Updating Cloud Array at index {start_index} for Device ID {device_id}")
                logging.debug(f"Cloud Array before update: {cloud_array[start_index:start_index + 10]}")

                # Update the array for this device with actual data as unsigned integers
                cloud_array[start_index:start_index + 10] = [
                    device_id,
                    int(parsed_data['Temperature']),
                    int(parsed_data['Humidity']),
                    int(parsed_data['PM1']),
                    int(parsed_data['PM2_5']),
                    int(parsed_data['PM10']),
                    int(parsed_data['CO2']),
                    int(parsed_data['VOC']),
                    int(parsed_data['NOx']),
                    int(parsed_data['AQI'])
                ]

                logging.debug(f"Cloud Array after update: {cloud_array[start_index:start_index + 10]}")

            except ValueError as e:
                logging.error(f"Device ID {device_id} not found in Cloud Array. Error: {e}")
        else:
            logging.debug(f"UniqueID {unique_id} not found in device mapping.")

    except Exception as e:
        logging.error(f"Error updating Cloud Array: {e}")

    return cloud_array


async def run_modbus_slave(modbus_array, modbus_device, context):
    identity = ModbusDeviceIdentification()
    identity.VendorName = 'Beko AeroSense'
    identity.ProductCode = 'OPAQ AQSN'
    identity.VendorUrl = 'http://https://www.bekocorporate.com/'
    identity.ProductName = 'OPAQ AQSN DWP'
    identity.ModelName = 'OPAQ AQSN Artlite LoRa Gateway'
    identity.MajorMinorRevision = '2.0'

    await StartAsyncSerialServer(
        context=context,
        identity=identity,
        framer=ModbusRtuFramer,
        port=modbus_device,
        baudrate=9600,
        parity='N',
        stopbits=2,
        bytesize=8,
        timeout=1
    )


async def main_task(context):
    global modbus_array
    global cloud_array


    try:
        with open("/usr/local/artlite-opaq-app/config/device_config.json", 'r') as f:
            unique_ids = json.load(f)
        logging.debug("Device configuration loaded successfully.")
    except IOError as e:
        logging.debug(f"Failed to read device configuration: {e}")
        exit(1)
    except json.JSONDecodeError as e:
        logging.debug(f"Failed to parse JSON: {e}")
        exit(1)

    device_id = get_device_id()
    logging.debug(f"Device ID: {device_id}")

    ebyte_type = unique_ids[device_id]["ebyteType"]

    logging.debug(f"Eybte Module: {ebyte_type}")

    # Initial mode setup
    set_mode(ebyte_type, "normal")
    set_mode(ebyte_type, "configuration")
    set_mode(ebyte_type, "normal")

    logging.debug(f"Checking if Device ID {device_id} is in the configuration.")
    logging.debug(f"Unique IDs: {unique_ids}")
    logging.debug(f"Device Type: {unique_ids[device_id]['devType']}")

    if device_id in unique_ids:
        logging.debug(f"Device ID {device_id} found in configuration.")

        if unique_ids[device_id]["devType"] == "sender":
            logging.debug("Device is in Sender Mode!")
            while True:
                try:
                    uniqueAddr_str = unique_ids[device_id]["customAddr"]
                    channel_str = unique_ids[device_id]["channel"]

                    channel = int(channel_str, 16)
                    unique_addr_hex = int(uniqueAddr_str, 16)

                    ADDL = unique_addr_hex & 0xFF
                    ADDH = (unique_addr_hex >> 8) & 0xFF

                    logging.debug(f"Channel Hex: {channel:#x}")
                    logging.debug(f"UniqueAddr Hex: {unique_addr_hex:#x}")
                    logging.debug(f"UniqueAddr Low Byte: {ADDL:#x}")
                    logging.debug(f"UniqueAddr High Byte: {ADDH:#x}")

                    # Attempt to configure LoRa
                    while True:
                        try:
                            with serial.Serial(lora_device, 9600, timeout=1) as ser:
                                configure_lora(ser, ebyte_type, ADDH, ADDL, channel)
                                ser.flushInput()
                                ser.flushOutput()

                                time.sleep(1)

                                send_data(ser, device_id)

                                end_time = time.time() + 5  # Calculate the end time (5 seconds from now)
                                
                                while time.time() < end_time:
                                    if ser.in_waiting > 0:  # Check if there's incoming data
                                        response = ser.readline().decode().strip()
                                        if response:
                                            logging.debug(f"Received message from gateway: {response}")
                                            handle_message(response, device_id)
                                    time.sleep(0.1)  # Small delay to avoid high CPU usage
                                
                                break  # Exit loop if successful
                        except Exception as e:
                            logging.debug(f"Error during LoRa configuration: {e}")
                            logging.debug("Applying fix and retrying...")
                            setup_pins("OFF")
                            setup_pins("ON")
                            set_mode(ebyte_type, "normal")
                            set_mode(ebyte_type, "configuration")
                            set_mode(ebyte_type, "normal")
                            time.sleep(2)  # Give it some time before retrying

                except KeyError as e:
                    logging.debug(f"Configuration for device ID {device_id} is incomplete: {e}")
                    break
                except serial.SerialException as e:
                    logging.debug(f"Serial communication error: {e}")
                    time.sleep(10)
                except Exception as e:
                    logging.debug(f"Unexpected error: {e}")
                    time.sleep(10)
        else:
            logging.debug("Device is in Receiver Mode!")
            uniqueAddr_str = unique_ids[device_id]["customAddr"]
            channel_str = unique_ids[device_id]["channel"]

            channel = int(channel_str, 16)
            unique_addr_hex = int(uniqueAddr_str, 16)

            ADDL = unique_addr_hex & 0xFF
            ADDH = (unique_addr_hex >> 8) & 0xFF
            logging.debug(f"Channel Hex: {channel:#x}")
            logging.debug(f"UniqueAddr Hex: {unique_addr_hex:#x}")
            logging.debug(f"UniqueAddr Low Byte: {ADDL:#x}")
            logging.debug(f"UniqueAddr High Byte: {ADDH:#x}")

            # Attempt to configure LoRa in receiver mode
            while True:
                try:
                    with serial.Serial(lora_device, 9600, timeout=1) as ser:
                        configure_lora(ser, ebyte_type, ADDH, ADDL, channel)
                    break  # Exit loop if successful
                except Exception as e:
                    logging.debug(f"Error during LoRa configuration: {e}")
                    logging.debug("Applying fix and retrying...")
                    setup_pins("OFF")
                    setup_pins("ON")
                    set_mode(ebyte_type, "normal")
                    set_mode(ebyte_type, "configuration")
                    set_mode(ebyte_type, "normal")
                    time.sleep(2)  # Give it some time before retrying

            try:
                reader, writer = await serial_asyncio.open_serial_connection(url=lora_device, baudrate=9600)

                buffer = bytearray()
                while True:
                    try:
                        data = await reader.read(1024)
                        buffer.extend(data)

                        while True:
                            try:
                                start_index = buffer.find(b'\xcb\xda')
                                end_index = buffer.find(b'\xbc\x0a')

                                if start_index != -1 and end_index != -1 and end_index > start_index:
                                    complete_message = buffer[start_index:end_index + 1]
                                    hex_data = complete_message.hex()
                                    logging.debug(f"Received Data: {hex_data}")

                                    try:
                                        parsed_data = parse_lora_data(hex_data)
                                        logging.debug(f"Parsed Data: {parsed_data}")
                                        log_with_size_limit("/usr/local/artlite-opaq-app/data/receiver_log_buffer.txt",
                                                            f"Parsed Data: {parsed_data}", 1000)
                                        modbus_array = update_modbus_array(modbus_array, parsed_data,
                                                                           device_mapping_path)
                                        logging.debug(
                                            f"Updated Modbus Array with size {len(modbus_array)}: {modbus_array}")

                                        # Update the Modbus holding registers with the new array
                                        store = context[2]  # Access the slave with address 2
                                        store.setValues(3, 0,
                                                        modbus_array)  # Update function code 3 (holding registers)

                                        cloud_array = update_cloud_array(cloud_array, parsed_data, device_mapping_path)
                                        logging.debug(
                                            f"Updated Cloud Array with size {len(cloud_array)}: {cloud_array}")

                                    except Exception as e:
                                        logging.error(f"Error processing parsed data: {e}")

                                    buffer = buffer[end_index + 1:]
                                else:
                                    break

                            except Exception as e:
                                logging.error(f"Error while processing buffer: {e}")
                                break

                        await asyncio.sleep(1)

                    except asyncio.CancelledError:
                        logging.debug("Task cancelled.")
                        break
                    except Exception as e:
                        logging.error(f"Error in main loop: {e}")
                        break

            except serial.SerialException as e:
                logging.error(f"Serial communication error: {e}")
            except KeyboardInterrupt:
                logging.debug("Stopped listening.")
            except Exception as e:
                logging.error(f"Unexpected error: {e}")


    else:
        logging.debug(f"Device ID {device_id} not found in configuration.")


async def run_all():
    global modbus_array
    global cloud_array
    global modbus_device
    global lora_device

    setup_pins("OFF")
    setup_pins("ON")

    lora_device = get_ttyUSB_device('FTDI Module Connected to Lora Module')
    modbus_device = get_ttyUSB_device('FTDI Module Connected to MODBUS Module')

    logging.debug(f"Lora Module Device: {lora_device}")
    logging.debug(f"MODBUS Module Device: {modbus_device}")

    if modbus_device is not None:

        modbus_array = initialize_modbus_array(device_mapping_path)
        logging.debug(f"Initialized Modbus Array with size {len(modbus_array)}: {modbus_array}")

        cloud_array = initialize_cloud_array(device_mapping_path)
        logging.debug(f"Initialized Cloud Array with size {len(cloud_array)}: {cloud_array}")

        # Start cloud setup in a separate thread
        cloud_thread = threading.Thread(target=cloud_tasks)
        cloud_thread.daemon = True
        cloud_thread.start()

        # Create a Modbus datastore with initial values
        hr_block = ModbusSequentialDataBlock(0, modbus_array)  # Create a holding register block
        store = ModbusSlaveContext(
            di=ModbusSequentialDataBlock(0, [0]*100),  # Discrete Inputs
            co=ModbusSequentialDataBlock(0, [0]*100),  # Coils
            hr=hr_block,  # Holding Registers
            ir=ModbusSequentialDataBlock(0, [0]*100)   # Input Registers
        )
        context = ModbusServerContext(slaves={2: store}, single=False)  # Set Slave Address to 2

        task1 = asyncio.create_task(run_modbus_slave(modbus_array, modbus_device, context))
        task2 = asyncio.create_task(monitor_modbus_array())
    else:
        logging.debug("Modbus operations are skipped due to no connected MODBUS module.")
        task1 = None
        task2 = None

    try:
        main_task_instance = asyncio.create_task(main_task(context if modbus_device else None))

        if task1 is not None:
            await asyncio.gather(task1, main_task_instance, task2)
        else:
            await main_task_instance  # Only run the main task if Modbus operations are skipped
    except asyncio.CancelledError:
        logging.debug("Tasks cancelled.")
    finally:
        logging.debug("Exiting run_all function.")


if __name__ == "__main__":
    try:
        asyncio.run(run_all())
    except KeyboardInterrupt:
        logging.debug("Received KeyboardInterrupt. Exiting.")
