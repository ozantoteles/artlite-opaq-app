import sys
import threading
import time
import logging
sys.path.insert(0, "/usr/local/OPAQ/")
from lib.lora_e220 import LoRaE220, print_configuration, Configuration, BROADCAST_ADDRESS
from Pin import Pin
from auxController import AuxController
from lora_e220_operation_constant import ResponseStatusCode, ModeType
from lora_e220_constants import FixedTransmission, RssiEnableByte
from arduino_iot_cloud import ArduinoCloudClient, Task
from secrets import DEVICE_ID, SECRET_KEY

# Configure the serial port
serial_port = '/dev/ttyUSB0'
baud_rate = 9600

aux_controller = AuxController('up')

m1_pin = "red_cntrl"
m0_pin = "green_cntrl"
vcc_pin = "lazer_cntrl"
ftdi_en_pin = "usb2_en"

m1_pin_obj = Pin(m1_pin, 0)
m0_pin_obj = Pin(m0_pin, 0)
time.sleep(1)
vcc_pin_obj = Pin(vcc_pin, 0)
time.sleep(1)
ftdi_en_pin_obj = Pin(ftdi_en_pin, 0)
time.sleep(1)
vcc_pin_obj.on()
time.sleep(1)
ftdi_en_pin_obj.on()
time.sleep(5)

lora = LoRaE220('900T22D', aux_pin=aux_controller, m0_pin=m0_pin, m1_pin=m1_pin)

code = lora.begin()
print("Initialization: {}", ResponseStatusCode.get_description(code))

# Set the configuration to default values and print the updated configuration to the console
# Not needed if already configured
configuration_to_set = Configuration('900T22D')
# Comment this section if you want test transparent transmission
configuration_to_set.ADDH = BROADCAST_ADDRESS  # Address of this receive no sender
configuration_to_set.ADDL = BROADCAST_ADDRESS  # Address of this receive no sender
configuration_to_set.CHAN = 25  # Address of this receive no sender
configuration_to_set.TRANSMISSION_MODE.fixedTransmission = FixedTransmission.FIXED_TRANSMISSION
# To enable RSSI, you must also enable RSSI on sender
configuration_to_set.TRANSMISSION_MODE.enableRSSI = RssiEnableByte.RSSI_ENABLED

code, confSetted = lora.set_configuration(configuration_to_set)
print("Set configuration: {}", ResponseStatusCode.get_description(code))

print("Waiting for messages...")

poll_interval = 1.0  # Polling interval in seconds (adjust based on message frequency)

# Cloud setup
rssi_value = 0

def update_rssi_value(client):
    global rssi_value
    logging.debug(f'RSSI Value: {rssi_value}')

def read_rssi_value(client, value_name=None):
    try:
        return rssi_value
    except Exception as e:
        logging.error(f'An error occurred: {e}')
        return 0

def setup_cloud():
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    logging.info("Starting AirQPi Application")
    
    client = ArduinoCloudClient(device_id=DEVICE_ID, username=DEVICE_ID, password=SECRET_KEY)
    
    client.register(Task("update_rssi_value", on_run=update_rssi_value, interval=10.0))
    
    client.register("rssi_value", value=0, on_read=read_rssi_value, interval=10.0)
    
    client.start()

def lora_receiver():
    global rssi_value
    while True:
        start_time = time.time()
        
        if lora.available() > 0:
            code, value, rssi = lora.receive_dict(rssi=True, size=100)
            print('RSSI:', rssi)

            if code == ResponseStatusCode.E220_SUCCESS:
                try:
                    print("Received data:", value)
                    # Update global RSSI value
                    rssi_value = rssi
                except (TypeError, KeyError) as e:
                    print("Error accessing received data:", e)
            else:
                print("Error Code:", ResponseStatusCode.get_description(code))
        
        end_time = time.time()
        elapsed_time = end_time - start_time
        sleep_duration = max(0, poll_interval - elapsed_time)
        time.sleep(sleep_duration)

# Start cloud setup in a separate thread
cloud_thread = threading.Thread(target=setup_cloud)
cloud_thread.daemon = True
cloud_thread.start()

# Start LoRa receiver
lora_receiver()
