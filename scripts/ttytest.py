import pyudev

# Define a mapping for USB paths to module names
module_mapping = {
    'usb2/2-1': 'FTDI Module Connected to Lora Module',
    'usb1/1-1': 'FTDI Module Connected to MODBUS Module',
}

context = pyudev.Context()

# Iterate through all ttyUSB devices
for device in context.list_devices(subsystem='tty', ID_BUS='usb'):
    # Get the parent device, which corresponds to the USB device
    parent = device.find_parent(subsystem='usb')

    if parent is not None:
        # Extract only the usbX/X-Y part of the device path for mapping
        usb_path_parts = parent.device_path.split('/')
        usb_path = '/'.join(usb_path_parts[-3:-1])

        # Check if this USB path is in our module mapping
        if usb_path in module_mapping:
            module_name = module_mapping[usb_path]
            print(f"{module_name} is on {usb_path} and the Device is {device.device_node}")
