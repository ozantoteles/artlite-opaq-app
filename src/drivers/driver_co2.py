# -*- coding: utf-8 -*-
import time
import argparse
import sys
import json
from datetime import datetime
import os

if sys.version_info[:2] == (3, 10):
    import smbus2 as smbus
else:
    import smbus

log_file = "/usr/local/artlite-opaq-app/data/co2_calibration_log.txt"

#for reference to Wuhan Cubic CM1107 sensor look at https://teams.microsoft.com/l/file/2ACD82CA-5781-4313-B232-071C023A9F8B?tenantId=ef5926db-9bdf-4f9f-9066-d8e7f03943f7&fileType=pdf&objectUrl=https%3A%2F%2Farcelik.sharepoint.com%2Fteams%2FC-AIRUCLA%2FShared%20Documents%2FGeneral%2FDonan%C4%B1m%2FDatasheet%2FCM1107.pdf&baseUrl=https%3A%2F%2Farcelik.sharepoint.com%2Fteams%2FC-AIRUCLA&serviceName=teams&threadId=19:dc5e5b9ac9cc4d49b2ef5ec90748f095@thread.skype&groupId=7cfa0503-c29f-4147-a5c7-e088994d1bfb

CM1107 = 0x31 # The slave address is 0x31

# Sensor limits
data_upper_limit = 5000
data_lower_limit = 1 # read function returns 0 in case of a problem

# Commands, Datasheet 2.1 Statement of Measuring Command
read_cmd = 0x01 # Read measured result of CO2, Datasheet 2.2 Measuring Result
azs_cmd = 0x10  # Open/ Close ABC and set ABC parameter, Datasheet 2.3 Auto Zero Specification Setting 
clb_cmd = 0x03  # Calibrate concentration value of CO2, Datasheet 2.4 Calibration
swv_cmd = 0x1E  # Read software version, Datasheet 2.5 Read the Serial Number of the Sensor
sn_cmd = 0x1F   # Read the serial number of the sensor, Datasheet 2.6 Read Software Version

def init(busNo):
    """
    Initialize an SMBus object with the specified bus number, get sensor ID, and return the bus.

    Parameters:
    busNo (int): The bus number to initialize the SMBus object with.

    Returns:
    bus (smbus.SMBus): The initialized SMBus object.

    """
    bus = smbus.SMBus(busNo)
    get_serial_number(bus)
    # get_software_version(bus)
    return bus

    
def read(bus):
    """
    This function takes an smbus.SMBus object as its argument and uses it to 
    communicate with the sensor. It sends the command to measure the result, 
    waits for the sensor to finish measuring, reads the data from the sensor, 
    extracts the CO2 measuring result and status byte from the data, 
    calculates the checksum, and returns the CO2 measuring result and status 
    byte as a tuple. If there is a checksum error, 
    the function raises a ValueError.
    
    Datasheet:
    The master device should send command of measuring result. 
    Send: 0x01
    Response: [0x01][DF0][DF1][DF2][CS]  
    Note: 
    1. Sensor starts measuring result status once receiving the command 0x01. 
    After this, all the data which I2C read will be such status format data, 
    until the sensor receives new command or re-powering on. 
    2. Data format, master device receives DF0 first, 
    and then receives CS at last.

    Remark: CO2 measuring result 
    Status Byte: [DF0] [DF1]
    Decimal Effective Value Range: 0 ~ 5,000 ppm
    Relative Value: 0 ~ 5,000 ppm

    CO2 measuring result: DF0*256+DF1, Fixed output is 550ppm during preheating period.

    Status Byte
    Bit7: Reserved
    Bit6:   1: Drift 
            0: Normal
    Bit5:   1: Light Aging
            0 Normal
    Bit4:   1: Non- calibrated
            0: Calibrated
    Bit3:   1: Less than Measurement Range
            0: Normal 
    Bit2:   1: Over Measurement Range
            0: Normal 
    Bit1:   1: Sensor Error
            0: Operating Normal
    Bit0:   1: Preheating
            0: Preheat complete

    Example: The master device reads some data: Read 3 bit. 
    0x01 0x03 0x20 0x00 0xDC
    CO2 measuring result = (0x03 0x20) hexadecimal = (800) decimal = 800 ppm
    Status bit: 0x00 means working normally
    [CS]= -(0x01+0x03+0x20+0x00)   Only keep the lowest bite.
    """
    
    """ bus.write_byte(CM1107,read_cmd) 
    time.sleep(0.5)
    data=bus.read_i2c_block_data(CM1107,read_cmd,4)
    bus.close()

    #print(data)

    CM1107data = 256*data[2]+data[3]
    #print(CM1107data)

    return CM1107data """

    # Send command to measure result
    bus.write_byte(CM1107,read_cmd)
    
    # Wait for the sensor to finish measuring
    time.sleep(0.5)
    
    # Read data from the sensor
    data = bus.read_i2c_block_data(CM1107, read_cmd, 5)
    
    bus.close()
    # print("data: ", data)

    # print("data[0]: ", data[0],
    #       "data[1]: ", data[1],
    #       "data[2]: ", data[2],
    #       "data[3]: ", data[3],
    #       "data[4]: ", data[4],)
    
    
    
    # Extract status byte from data
    status_byte = data[3]
    bit7 = (status_byte & 0b10000000) >> 7
    bit6 = (status_byte & 0b01000000) >> 6
    bit5 = (status_byte & 0b00100000) >> 5
    bit4 = (status_byte & 0b00010000) >> 4
    bit3 = (status_byte & 0b00001000) >> 3
    bit2 = (status_byte & 0b00000100) >> 2
    bit1 = (status_byte & 0b00000010) >> 1
    bit0 = status_byte & 0b00000001

    # Extract CO2 measuring result from data
    if bit1 == 1:
        print("Error: Sensor error detected")
        return -999
    elif bit2 == 1:
        print("Error: Measurement range over range")
        return data_upper_limit
    elif bit3 == 1:
        print("Error: Measurement range less than range")
        return data_lower_limit
    else:
        co2 = (data[1] << 8) + data[2]
        # print("co2: ", co2)
        return co2 

    # Print the status bits (optional)
    # print("Status Byte: {}".format(status_byte))
    # print("Bit 7: Reserved: {}".format(bit7))
    # print("Bit 6: Drift: {}".format('Detected' if bit6 == 1 else 'Not detected'))
    # print("Bit 5: Light Aging: {}".format('Detected' if bit5 == 1 else 'Not detected'))
    # print("Bit 4: Calibration: {}".format('Not calibrated' if bit4 == 1 else 'Calibrated'))
    # print("Bit 3: Measurement Range: {}".format('Less than range' if bit3 == 1 else 'Normal'))
    # print("Bit 2: Measurement Range: {}".format('Over range' if bit2 == 1 else 'Normal'))
    # print("Bit 1: Sensor Error: {}".format('Error' if bit1 == 1 else 'Normal'))
    # print("Bit 0: Preheating: {}".format('In progress' if bit0 == 1 else 'Complete'))

    # Sensor checksum is not valid for current hw/sw version, 
    # checksum control would be implemented later
    
    # Calculate checksum
    # cs = -(sum(data) & 0xFF)
    
    # Check if checksum is correct
    # if cs != data[4]:
    #     print("cs: ", cs)
    #     print("data[3]: ", data[4])
    #     raise ValueError("Checksum error")

    # return co2, status_byte # status byte handling is done inside the function for now

def calculate_checksum(data):
    # Calculate the sum of the data bytes
    total = sum(data)
    # Compute the checksum as the negative of the total, keeping only the lowest byte
    checksum = -total & 0xFF
    return checksum

def log_calibration(log_file, target_ppm, command):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # Check if the file exists
    file_exists = os.path.isfile(log_file)
    
    with open(log_file, mode='a') as file:
        if file_exists:
            file.write("\n")  # Add a new line before the next log entry if file already exists
        
        # Write the log entry in one line
        file.write("{} | Target ppm: {} | Calibration Result Command: {}".format(timestamp, target_ppm, command))
        print("Wrote to file " + log_file)
    
def calibrate_sensor(bus,target_ppm):
    if not (400 <= target_ppm <= 1500):
        print("Target ppm should be between 400 and 1500!")
        return "error"
 
    # Convert target_ppm to high and low bytes
    DF0 = (target_ppm >> 8) & 0xFF # high byte
    DF1 = target_ppm & 0xFF # low byte
 
    # Send the command to the sensor
    bus.write_i2c_block_data(CM1107, clb_cmd, [DF0, DF1])
    print("Sent: Command={}, DF0={}, DF1={}".format(clb_cmd, DF0, DF1))
    calculated_checksum = calculate_checksum([clb_cmd, DF0, DF1])
    print("Checksum: ",calculated_checksum)
    # Wait for the sensor to respond
    time.sleep(1)
    # Read the response (should be 4 bytes)
    response = bus.read_i2c_block_data(CM1107, clb_cmd, 4)
 
    if len(response) == 4:
        print("Received: Command={}, DF0={}, DF1={}, CS={}".format(response[0], response[1], response[2], response[3]))
 
        # Verify checksum 
        if response[3] == (calculated_checksum):  
            print("Checksum valid")
            log_calibration(log_file, target_ppm, response)
            return response
        else:
            print("Checksum invalid")
            return "error"
 
    else:
        print("Error: Unexpected response length")
        return "error"

        
def get_serial_number(bus):
    """
    Sends the command 0x1F to the CM1107 sensor to get the serial number.

    Args:
        bus (smbus.SMBus): The I2C bus object to communicate with the sensor.

    Returns:
        str: The 20-digit serial number of the sensor.

    Datasheet:
    Send: 0x1F 
    Response: [0x1F] [DF0] [DF1] [DF2] [DF3] [DF4] [DF5] [DF6] [DF7] [DF8] [DF9] [CS] 
    Note: 
    1. Sensor starts device code output status once receiving the command 0x1F. 
    After this, all the data which I2C read will be such status format data, 
    until the sensor receives new command or re-powering on. 
    2. Data format, the master device receives [DF0] first, and then receives [CS] at last. 
    High bit in front. 
    [DF0][DF1]: Integer type 1 (0-9999)
    [DF2][DF3]: Integer type 2 (0-9999)
    [DF4][DF5]: Integer type 3 (0-9999)
    [DF6][DF7]: Integer type 4 (0-9999)
    [DF8][DF9]: Integer type 5 (0-9999)
    3. The five-integer types constitute serial number of 20 digits. 
    """

    # Send the command 0x1F to the sensor
    bus.write_byte(CM1107, sn_cmd)

    # Read the response data
    data = bus.read_i2c_block_data(CM1107, sn_cmd, 32)

    # Extract the 5 integers from the response data
    int1 = (data[1] << 8) | data[2]
    int2 = (data[3] << 8) | data[4]
    int3 = (data[5] << 8) | data[6]
    int4 = (data[7] << 8) | data[8]
    int5 = (data[9] << 8) | data[10]

    # Combine the 5 integers to form the serial number
    serial_number = '{:04d}{:04d}{:04d}{:04d}{:04d}'.format(int1, int2, int3, int4, int5)
    # print("CM1107 Serial Number: ", serial_number)

    return serial_number

def get_software_version(bus):
    """
    Datasheet:
    Send: 0x1E Response: [0x1E] [DF0] [DF1] [DF2] [DF3] [DF4] [DF5] [DF6] [DF7] [DF8] [DF9] [CS] 
    Note:  
    1. Sensor starts software version output status once receiving the command 0x1E. 
    After this, all the data which I2C read will be such status format data, 
    until the sensor receives new command or re-powering on. 
    2. Data format, the master device receives DF0 first, and then receives CS at last. 
    [DF0] ... [DF9] is ASCII. 
    """

    # Send the command 0x1F to the sensor
    bus.write_byte(CM1107, swv_cmd)

    # Read the response data
    data = bus.read_i2c_block_data(CM1107, swv_cmd, 11)
    # print("data: ", data)

    # convert the ASCII data to a string
    software_version = ''.join([chr(d) for d in data[1:-1]])
    # print("CM1107 Software Verson: ", software_version)

    return software_version

def ftc_mode(file):

    bus = init(0)
    serial_number = get_serial_number(bus)
    data = read(bus)
    
    
    print('''Data: %d ''' % data)
    
    output_json = {
        "serial_number": str(serial_number),
        "sensor_value": str(data)
    }

    with open(file, 'w') as f:
        f.write(json.dumps(output_json))

    print('''Data: %d ''' % data)
    if data < data_upper_limit and data > data_lower_limit:
        print("sensor value(s) are normal, OK")
        sys.exit(0)
    else:
        print("sensor value(s) are not within desired limits, FAIL")
        sys.exit(1)

def main():

    msg = "CM1107 CO2 Sensor Python Module"
    help_msg = "RUN_MODE options: normal ftc, default:normal"
    help_msg_output_file = "OUTPUT_FILE: specify file path to write serial number and the other data, default: /tmp/sensor_co2_out"

    parser = argparse.ArgumentParser(description=msg)

    parser.add_argument("-r", "--run_mode", type=str, default="normal", required=False, help = help_msg)      
    parser.add_argument("-o", "--output_file", type=str, default="/tmp/sensor_co2_out", required=False, help = help_msg_output_file)
    parser.add_argument("-t", "--target_ppm", type=str, default=400, required=False, help = help_msg_output_file)

    args = parser.parse_args()

    if args.run_mode == "ftc":
        ftc_mode(args.output_file)
        
    elif args.run_mode == "calib":
        print("Calibration mode is active")
        print("args.target_ppm: ",args.target_ppm)
        bus = init(0)
        response = calibrate_sensor(bus,int(args.target_ppm))
        print("Calibration response: ",response)
    
    bus = init(0)
    co2_data = read(bus)

    return 0

if __name__ == '__main__':
    main() 
        
