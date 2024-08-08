import sys
sys.path.insert(0, "/usr/local/artlite-opaq-app/")
from lib.lora_e220 import LoRaE220, print_configuration, Configuration
from Pin import Pin
from auxController import AuxController
import serial
import time
from lora_e220_operation_constant import ResponseStatusCode, ModeType

# Configure the serial port
serial_port = '/dev/ttyUSB0'  
baud_rate = 9600

aux_controller = AuxController('up')

m1_pin = "red_cntrl"
m0_pin = "green_cntrl"
vcc_pin = "lazer_cntrl"
ftdi_en_pin = "usb2_en"

m1_pin_obj = Pin(m1_pin,0)
m0_pin_obj = Pin(m0_pin,0)
time.sleep(1)
vcc_pin_obj = Pin(vcc_pin,0)
time.sleep(1)
ftdi_en_pin_obj = Pin(ftdi_en_pin,0)
time.sleep(1)
vcc_pin_obj.on()
time.sleep(1)
ftdi_en_pin_obj.on()
time.sleep(5)

lora = LoRaE220('900T22D', aux_pin=aux_controller, m0_pin=m0_pin, m1_pin=m1_pin)

code = lora.begin()
print("Initialization: {}", ResponseStatusCode.get_description(code))

code, configuration = lora.get_configuration()

print("Retrieve configuration: {}", ResponseStatusCode.get_description(code))

print_configuration(configuration)

#
# Initialization: {} Success
# Retrieve configuration: {} Success
# ----------------------------------------
# HEAD :  0xc1   0x0   0x8
#
# AddH :  0x0
# AddL :  0x0
#
# Chan :  23  ->  433
#
# SpeedParityBit :  0b0  ->  8N1 (Default)
# SpeedUARTDatte :  0b11  ->  9600bps (default)
# SpeedAirDataRate :  0b10  ->  2.4kbps (default)
#
# OptionSubPacketSett:  0b0  ->  200bytes (default)
# OptionTranPower :  0b0  ->  22dBm (Default)
# OptionRSSIAmbientNo:  0b0  ->  Disabled (default)
#
# TransModeWORPeriod :  0b11  ->  2000ms (default)
# TransModeEnableLBT :  0b0  ->  Disabled (default)
# TransModeEnableRSSI:  0b0  ->  Disabled (default)
# TransModeFixedTrans:  0b0  ->  Transparent transmission (default)
# ----------------------------------------
