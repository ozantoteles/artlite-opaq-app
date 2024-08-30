import pyudev

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
