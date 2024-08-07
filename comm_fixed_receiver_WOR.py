import sys
sys.path.insert(0, "/usr/local/OPAQ/")
from lib.lora_e220 import LoRaE220, print_configuration, Configuration, BROADCAST_ADDRESS
from Pin import Pin
from auxController import AuxController
import serial
import time
from lora_e220_operation_constant import ResponseStatusCode, ModeType
from lora_e220_constants import FixedTransmission, RssiEnableByte

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
print("Initialization code:", code)
print("Initialization:", ResponseStatusCode.get_description(code))

configuration_to_set = Configuration('900T22D')
configuration_to_set.ADDH = BROADCAST_ADDRESS  # Set to broadcast address
configuration_to_set.ADDL = BROADCAST_ADDRESS  # Set to broadcast address
configuration_to_set.CHAN = 25                 # Ensure this channel matches senders
configuration_to_set.TRANSMISSION_MODE.fixedTransmission = FixedTransmission.FIXED_TRANSMISSION
configuration_to_set.TRANSMISSION_MODE.enableRSSI = RssiEnableByte.RSSI_ENABLED

code, confSetted = lora.set_configuration(configuration_to_set)
print("Set configuration code:", code)
print("Set configuration:", ResponseStatusCode.get_description(code))
print_configuration(confSetted)

code, configuration = lora.get_configuration()
print("Retrieve configuration code:", code)
print("Retrieve configuration:", ResponseStatusCode.get_description(code))
print_configuration(configuration)

print("Waiting for messages...")

lora.set_mode(ModeType.MODE_2_WOR_RECEIVER)

while True:
    if lora.available() > 0:
        code, value, rssi = lora.receive_dict(rssi=True, size=100)
        print("RSSI:", rssi)
        print("Receive message code:", code)
        print("Receive message description:", ResponseStatusCode.get_description(code))

        if code == ResponseStatusCode.E220_SUCCESS:
            try:
                print("Received data:", value)
            except (TypeError, KeyError) as e:
                print("Error accessing received data:", e)
        else:
            print("Error Code:", ResponseStatusCode.get_description(code))

    # Debugging: Check the state of the pins
    print("M0 pin state:", m0_pin_obj.value)
    print("M1 pin state:", m1_pin_obj.value)

    time.sleep(1)
