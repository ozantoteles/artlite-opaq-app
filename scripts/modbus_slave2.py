import asyncio
import logging
from pymodbus.datastore import ModbusSlaveContext, ModbusServerContext, ModbusSequentialDataBlock
from pymodbus.server.async_io import StartAsyncSerialServer
from pymodbus.transaction import ModbusRtuFramer
from pymodbus.device import ModbusDeviceIdentification

import pyudev
import json

device_mapping_path = "/usr/local/artlite-opaq-app/config/device_mapping.json"

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

# Example usage:
lora_device = get_ttyUSB_device('FTDI Module Connected to Lora Module')
modbus_device = get_ttyUSB_device('FTDI Module Connected to MODBUS Module')

print(f"Lora Module Device: {lora_device}")
print(f"MODBUS Module Device: {modbus_device}")

# Set up logging for debugging
logging.basicConfig()
log = logging.getLogger()
log.setLevel(logging.DEBUG)

async def run_modbus_slave(modbus_array):
    # Create a Modbus datastore with initial values
    # Initialize holding registers from address 1 to 10
    store = ModbusSlaveContext(
        di=ModbusSequentialDataBlock(0, [0]*100),  # Discrete Inputs
        co=ModbusSequentialDataBlock(0, [0]*100),  # Coils
        hr=ModbusSequentialDataBlock(1, modbus_array),  # Holding Registers from address 1 to 10
        ir=ModbusSequentialDataBlock(0, [0]*100)   # Input Registers
    )
    context = ModbusServerContext(slaves={2: store}, single=False)  # Set Slave Address to 2

    # Optionally, set up device identification (not necessary for basic testing)
    identity = ModbusDeviceIdentification()
    identity.VendorName = 'YourVendorName'
    identity.ProductCode = 'YourProductCode'
    identity.VendorUrl = 'http://yourvendorurl.com'
    identity.ProductName = 'YourProductName'
    identity.ModelName = 'YourModelName'
    identity.MajorMinorRevision = '1.0'

    # Start the Modbus slave server with the RTU framer
    await StartAsyncSerialServer(
        context=context,
        identity=identity,  # Optional, only needed if you want to test Modbus device identification
        framer=ModbusRtuFramer,  # Use Modbus RTU framer
        port=modbus_device,  # Use the correct COM port for the FTDI adapter
        baudrate=9600,
        parity='N',
        stopbits=2,
        bytesize=8,
        timeout=1
    )

if __name__ == "__main__":
    modbus_array = initialize_modbus_array(device_mapping_path)
    logging.debug(f"Initialized Modbus Array with size {len(modbus_array)}: {modbus_array}")
    asyncio.run(run_modbus_slave(modbus_array))
