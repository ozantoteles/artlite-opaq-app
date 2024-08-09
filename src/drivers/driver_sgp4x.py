import time
import os, csv
import argparse
import json
import sys
from sensirion_i2c_driver import LinuxI2cTransceiver, I2cConnection
from sensirion_i2c_sgp4x import Sgp40I2cDevice
from sensirion_i2c_sgp4x import Sgp41I2cDevice
from subprocess import check_output



if sys.version_info[:3] == (2,7,14) or sys.version_info[:3] == (3,5,3):
    py3x_version = str(5)
else:
    py3x_version = str(10) 


# Sensor limits
data_upper_limit = 500
data_lower_limit = 0

data_raw_upper_limit = 65535
data_raw_lower_limit = 0
#for reference to Sensirion SGP30 sensor look at https://teams.microsoft.com/l/file/6BAC2A32-F520-47BF-9E64-BACEF629B08D?tenantId=ef5926db-9bdf-4f9f-9066-d8e7f03943f7&fileType=pdf&objectUrl=https%3A%2F%2Farcelik.sharepoint.com%2Fteams%2FC-AIRUCLA%2FShared%20Documents%2FGeneral%2FDonan%C4%B1m%2FDatasheet%2FSensirion_Gas_Sensors_SGP30_Datasheet.pdf&baseUrl=https%3A%2F%2Farcelik.sharepoint.com%2Fteams%2FC-AIRUCLA&serviceName=teams&threadId=19:dc5e5b9ac9cc4d49b2ef5ec90748f095@thread.skype&groupId=7cfa0503-c29f-4147-a5c7-e088994d1bfb
#SGP30 address, page:8

SGP4x_ADDR = 0x59
SGP4x_ADDR_BUS_NO = 0

vocBufferSize = 5000
vocBufferFolder = "/home/cairapp/VOC/"
vocBufferFile = vocBufferFolder + "vochistory.csv" 

noxBufferSize = 5000
noxBufferFolder = "/home/cairapp/NOX/"
noxBufferFile = noxBufferFolder + "noxhistory.csv" 


def init(busNO, sensorName, sensorModel, conditioning=False):
    busNo_addr = '/dev/i2c-'+str(busNO)
    i2c_transceiver_sgp = LinuxI2cTransceiver(busNo_addr)
    try:
        if sensorModel == "SGP40":
            sgp4x = Sgp40I2cDevice(I2cConnection(i2c_transceiver_sgp), slave_address=SGP4x_ADDR)
        elif sensorModel == "SGP41":
            sgp4x = Sgp41I2cDevice(I2cConnection(i2c_transceiver_sgp), slave_address=SGP4x_ADDR)

            if conditioning:
                # Run  conditioning for 10 seconds
                for _ in range(10):
                    time.sleep(1)
                    sraw_voc = sgp4x.conditioning()
                    # use default formatting for printing output:

                time.sleep(1) # After calling the conditioning command and after a subsequent minimum waiting time of 50 ms
    except:

        i2c_transceiver_sgp.close()
        return -1, -1       


    
    return sgp4x, i2c_transceiver_sgp
    

def read(sensor, i2cTransceiver, sensorModel, temperature = 25.0, humidity = 50.0):

    
    sgp4x_data = {}
    if sensorModel == "SGP40":
        sraw_voc = sensor.measure_raw(temperature, humidity)


        cmd = "python3." + py3x_version + " /usr/local/artlite-opaq-app/src/drivers/sgpidx_p3.py " + "VOC" + " " + str(sraw_voc) + " " + str(vocBufferSize) + " " + vocBufferFolder + " " + vocBufferFile
        VOCindex = check_output(cmd, shell=True)
        voc_data = int(VOCindex)
        nox_data = -999
        
        i2cTransceiver.close()
    
    elif sensorModel == "SGP41":
        sraw_voc, sraw_nox = sensor.measure_raw(temperature, humidity)


        cmd = "python3." + py3x_version + " /usr/local/artlite-opaq-app/src/drivers/sgpidx_p3.py " + "VOC" + " " + str(sraw_voc) + " " + str(vocBufferSize) + " " + vocBufferFolder + " " + vocBufferFile
        VOCindex = check_output(cmd, shell=True)
        
        cmd = "python3." + py3x_version + " /usr/local/artlite-opaq-app/src/drivers/sgpidx_p3.py " + "NOX" + " " + str(sraw_nox) + " " + str(noxBufferSize) + " " + noxBufferFolder + " " + noxBufferFile
        NOXindex = check_output(cmd, shell=True)

        voc_data = int(VOCindex)
        nox_data = int(NOXindex)
        raw_voc = int(str(sraw_voc))
        raw_nox = int(str(sraw_nox))
        
        i2cTransceiver.close()
    
    return voc_data, nox_data, raw_voc, raw_nox
    
def ftc_mode(file, sensor_model="SGP41"):
    bus, i2c_transceiver_sgp = init(SGP4x_ADDR_BUS_NO, "SGP4x", sensor_model, conditioning=True)
    serial_number = bus.get_serial_number()
    
   
    data_VOC, data_NOX, data_raw_VOC, data_raw_NOX = read(bus, i2c_transceiver_sgp, sensor_model)

    print('''Data raw TVOC: %d ''' % data_raw_VOC)
    print('''Data TVOC: %d ''' % data_VOC)
    print('''Data raw NOX: %d ''' % data_raw_NOX)
    print('''Data NOX: %d ''' % data_NOX)

    output_json = {
        "serial_number": str(serial_number),
        "VOC_raw": str(data_raw_VOC),
        "VOC": str(data_VOC),
        "NO2_raw": str(data_raw_NOX),
        "NO2": str(data_NOX)
    }

        
    with open(file, 'w') as f:
        f.write(json.dumps(output_json))  
    
    if data_VOC <= data_upper_limit and data_VOC >= data_lower_limit  and \
        data_NOX <= data_upper_limit and data_NOX >= data_lower_limit and \
        data_raw_VOC <= data_raw_upper_limit and data_raw_VOC >= data_raw_lower_limit and \
        data_raw_NOX<= data_raw_upper_limit and data_raw_NOX >= data_raw_lower_limit:
        print("sensor value(s) are normal, OK")
        sys.exit(0)
    else:
        print("sensor value(s) are not within desired limits, FAIL")
        sys.exit(1)       
    
def main():

    # FTC
    msg = "VOC Sensor Python Module"
    help_msg = "RUN_MODE options: normal ftc, default:normal"
    help_msg_output_file = "OUTPUT_FILE: specify file path to write serial number and the other data, default: /tmp/sensor_voc_out"

    parser = argparse.ArgumentParser(description=msg)

    parser.add_argument("-r", "--run_mode", type=str, default="normal", required=False, help = help_msg)
    parser.add_argument("-o", "--output_file", type=str, default="/tmp/sensor_voc_out", required=False, help = help_msg_output_file)      

    args = parser.parse_args()

    if args.run_mode == "ftc":
        ftc_mode(args.output_file)

    # Sensor init and read
    try:
        sensor_model = "SGP41"

        if sensor_model == "SGP40":
            sgp40, i2c_transceiver_sgp = init(SGP4x_ADDR_BUS_NO, "SGP40", sensor_model, conditioning=True)
            sgp40_data = read(sgp40, i2c_transceiver_sgp, sensor_model)

        elif sensor_model == "SGP41":
            sgp41, i2c_transceiver_sgp  = init(SGP4x_ADDR_BUS_NO, "SGP41", sensor_model, conditioning=True)
            sgp41_data = read(sgp41, i2c_transceiver_sgp, sensor_model)

        
    
    except Exception as e:
       print('An error occurred: %s', str(e))

    return 0

if __name__ == '__main__':
    main() 
