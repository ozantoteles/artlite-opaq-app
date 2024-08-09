# -*- coding: utf-8 -*-
import time
import argparse
import sys
import json
import logging

sys.path.insert(0, "/usr/local/cair-app/")
from config import log


#for reference to SGX MICS-6814 sensor look at https://teams.microsoft.com/l/file/F1AF367D-E383-4058-BF6C-B59D0514E52A?tenantId=ef5926db-9bdf-4f9f-9066-d8e7f03943f7&fileType=pdf&objectUrl=https%3A%2F%2Farcelik.sharepoint.com%2Fteams%2FC-AIRUCLA%2FShared%20Documents%2FGeneral%2FDonan%C4%B1m%2FDatasheet%2FSGX-6814-rev-8.pdf&baseUrl=https%3A%2F%2Farcelik.sharepoint.com%2Fteams%2FC-AIRUCLA&serviceName=teams&threadId=19:dc5e5b9ac9cc4d49b2ef5ec90748f095@thread.skype&groupId=7cfa0503-c29f-4147-a5c7-e088994d1bfb

#default adc paths for cair
adcPATH_CO  = "/sys/bus/iio/devices/iio:device0/in_voltage0_raw"
adcPATH_NH3 = "/sys/bus/iio/devices/iio:device0/in_voltage6_raw"
adcPATH_NO2 = "/sys/bus/iio/devices/iio:device0/in_voltage8_raw"

# Sensor limits
CO_data_upper_limit = 15
CO_data_lower_limit = 0
NH3_data_upper_limit = 5000
NH3_data_lower_limit = 0
NO2_data_upper_limit = 500
NO2_data_lower_limit = 0

def init(pathCO_IN, pathNH3_IN, pathN02_IN):

    adcPATH_CO = pathCO_IN
    adcPATH_NH3 = pathNH3_IN
    adcPATH_NO2 = pathN02_IN
    return 0

# for formulatons and load resitance values look at  https://arcelik.sharepoint.com/teams/C-AIRUCLA/_layouts/15/Doc.aspx?OR=teams&action=edit&sourcedoc={8A6729F8-137A-4114-802A-99A298283AB4}

def readADC_CO():
    with open(adcPATH_CO, 'r') as f:
        data = f.read()
    
    #CO FORMULATIONS
        ##CO_ppm=0.41366 * float(data) -345.41 +1
        CO_ppm=pow(float(data)/4.0, -1.179) * 4.385
    
        return CO_ppm

def readADC_NH3():
    with open(adcPATH_NH3, 'r') as f:
        data = f.read()
    
    #NH3 FORMULATIONS
        #NH3_ppm=0.09474 * float(data) -79.108 +1
        NH3_ppm=pow(float(data)/4.0, -1.67) / 1.47
        
    return NH3_ppm

def readADC_NO2():
    with open(adcPATH_NO2, 'r') as f:
        data = f.read()
    
    #NO2 FORMULATIONS
        #NO2_ppm=0.00399 * float(data) -5.0228+0.05
        NO2_ppm=pow(float(data)/4.0, 1.007) / 6.855
        
    return NO2_ppm

def read():
    dataCO = readADC_CO()
    dataNH3 = readADC_NH3()
    dataNO2 = readADC_NO2()
    
    return dataCO, dataNH3, dataNO2

def ftc_mode(file):

    bus = init(adcPATH_CO, adcPATH_NH3, adcPATH_NO2)
    dataCO, dataNH3, dataNO2 = read()
    log.info('CO: %f ', dataCO)
    log.info('NH3: %f ', dataNH3)
    log.info('NO2: %f ', dataNO2)
    if  dataCO < CO_data_upper_limit and dataCO > CO_data_lower_limit and \
        dataNH3 < NH3_data_upper_limit and dataNH3 > NH3_data_lower_limit and \
        dataNO2 < NO2_data_upper_limit and dataNO2 > NO2_data_lower_limit      \
        :
        log.info("sensor value(s) are normal, OK")

        output_json = {
            "CO": str(dataCO),
            "NH3": str(dataNH3),
            "NO2": str(dataNO2)
        }

        with open(file, 'w') as f:
            f.write(json.dumps(output_json))

        sys.exit(0)
    else:
        log.info("sensor value(s) are not within desired limits, FAIL")
        sys.exit(1)

def main():

    msg = " AMISC-6814 Sensor Python Module  "
    help_msg = "RUN_MODE options: normal ftc, default:normal"
    help_msg_output_file = "OUTPUT_FILE: specify file path to write serial number and the other data, default: /tmp/sensor_voc_out"

    parser = argparse.ArgumentParser(description=msg)

    parser.add_argument("-r", "--run_mode", type=str, default="normal", required=False, help = help_msg)
    parser.add_argument("-o", "--output_file", type=str, default="/tmp/sensor_voc_out", required=False, help = help_msg_output_file)     

    args = parser.parse_args()

    if args.run_mode == "ftc":
        ftc_mode(args.output_file)

    init(adcPATH_CO, adcPATH_NH3, adcPATH_NO2)

    dataCO, dataNH3, dataNO2 = read()
    log.info("dataCO, dataNH3, dataNO2: %f, %f, %f",dataCO, dataNH3, dataNO2)
    time.sleep(1)
    # while 1:
        
        # dataCO, dataNH3, dataNO2 = read()
        # time.sleep(1)
    
    # return 0

if __name__ == '__main__':
    main()
