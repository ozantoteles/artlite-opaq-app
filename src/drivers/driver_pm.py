# -*- coding: utf-8 -*-
#for reference to Wuhan Cubic PM2008 sensor look at https://teams.microsoft.com/l/file/04F919D6-0A21-4685-A442-C98CF365C483?tenantId=ef5926db-9bdf-4f9f-9066-d8e7f03943f7&fileType=pdf&objectUrl=https%3A%2F%2Farcelik.sharepoint.com%2Fteams%2FC-AIRUCLA%2FShared%20Documents%2FGeneral%2FDonan%C4%B1m%2FDatasheet%2FPM2008.pdf&baseUrl=https%3A%2F%2Farcelik.sharepoint.com%2Fteams%2FC-AIRUCLA&serviceName=teams&threadId=19:dc5e5b9ac9cc4d49b2ef5ec90748f095@thread.skype&groupId=7cfa0503-c29f-4147-a5c7-e088994d1bfb
import argparse
import sys
import json

if sys.version_info[:2] == (3, 10):
    import smbus2 as smbus
else:
    import smbus
    


# I2C address
PM2008 = (0x50 >> 1)

# Sensor limits
data_upper_limit = 300
data_lower_limit = 0

# Prepare Open single measurement command and check sum bytes
# Datasheet 3.1 Send Command Data page:17
# Send by main controlled board:
# START+WRITE+ACK+P1+ACK+P2+ACK... +P7+ACK+STOP
p1=0x16 # Frame header
p2=7    # Number of byte, not including length of device address (From P1 to P7, 7 bytes in total)
p3=2    # Data 1
p4=0xFF # Data 2, high byte
p5=0xFF # Data 2, low byte
p6=0xFF # Data 3
p7=p1^p2^p3^p4^p5^p6    # Data check code

def delay_sec(count):
    while(count>1):
        count=count-1

def init(busNo):
    
    bus = smbus.SMBus(busNo)
    return bus

def read(bus):
    """
    Datasheet 3.2 Read Data Command
    Send by main controlled board:
    START+READ+ACK+P1+ACK+P2+ACK+....+P32+NACK+STOP

    "Data"	"Byte Content"	"Description"
    "Device address"	"Sensor address and read/write command"	"This byte is 0x51 when read data"
    P1	0x16	Frame header
    P2	Frame length	Number of bytes, not including length of device address (from P1 to P32, 32 bytes in total)
    P3	Sensor status	Close: 1; Alarm: 7; Measuring: 2; Data stable: 0x80 (only for dynamic or timing measuring mode). Other data is invalid.(Check 3.3 detailed introduction for every kinds of measurement mode)
    P4	Data 1, high byte	The measuring mode of sensor as: Single measuring mode: 2; Continuous measuring mode: 3 Dynamic measuring mode: 5; Timing measuring mode: >= 60 (means measuring period)
    P5	Data 1, low byte	
    P6	Data 2, high byte	Calibration coefficient: (Range: 70-150, Corresponding: 0.7-1.5）
    P7	Data 2, low byte	
    P8	Data 3, high byte	PM1.0 concentration, unit: ug/m3, GRIMM
    P9	Data 3, low byte	
    P10	Data 4, high byte	PM2.5 concentration, unit: ug/m3, GRIMM
    P11	Data 4, low byte
    P12	Data 5, high byte	PM10 concentration, unit: ug/m3, GRIMM
    P13	Data 5, low byte	
    P14	Data 6, high byte	PM1.0 concentration, unit: ug/m3, TSI
    P15	Data 6, low byte	
    P16	Data 7, high byte	PM2.5 concentration, unit: ug/m3, TSI
    P17	Data 7, low byte	
    P18	Data 8, high byte	PM10 concentration, unit: ug/m3 , TSI
    P19	Data 8, low byte	
    P20	Data 9, high byte	Number of PM0.3, unit: pcs/0.1L
    P21	Data 9, low byte	
    P22	Data 10, high byte	Number of PM0.5, unit: pcs/0.1L
    P23	Data 10, low byte	
    P24	Data 11, high byte	Number of PM1.0, unit: pcs/0.1L
    P25	Data 11, low byte	
    P26	Data 12, high byte	Number of PM2.5, unit: pcs/0.1L
    P27	Data 12, low byte	
    P28	Data 13, high byte	Number of PM5.0, unit: pcs/0.1L
    P29	Data 13, low byte	
    P30	Data 14, high byte	Number of PM10, unit: pcs/0.1L
    P31	Data 14, low byte	P32	Data check code Check code = (P1^P2^...^P31)
    """  
    #send measure command, page:17
    bus.write_i2c_block_data(PM2008,p1,[p2,p3,p4,p5,p6,p7])
    delay_sec(0xFFFF)
    #read sensor values, page:18
    data=bus.read_i2c_block_data(PM2008,0x00,32)
    bus.close()
    #print(data)
    #print("PM2008 Status Byte: ",data[2])
    #print("PM1.0 GRIMM:",256*data[7]+data[8])
    #print("PM2.5 GRIMM:",256*data[9]+data[10])
    #print("PM 10 GRIMM:",256*data[11]+data[12])
    #print("PM1.0 TSI  :",256*data[13]+data[14])
    #print("PM2.5 TSI  :",256*data[15]+data[16])
    #print("PM 10 TSI  :",256*data[17]+data[18])
    #print("PM0.3 L    :",256*data[19]+data[20])
    #print("PM0.5 L    :",256*data[21]+data[22])
    #print("PM1.0 L    :",256*data[23]+data[24])
    #print("PM2.5 L    :",256*data[25]+data[26])
    #print("PM  5 L    :",256*data[27]+data[28])
    #print("PM 10 L    :",256*data[29]+data[30])
    #print()

    # Check status byte and return -999 if not measuring
    if data[2] != 2:
        pm2008SensorVals = {
            "CAIRPM2008_1.0_GRIMM_LEVEL": -999,
            "CAIRPM2008_2.5_GRIMM_LEVEL": -999,
            "CAIRPM2008_10_GRIMM_LEVEL": -999,
            "CAIRPM2008_1.0_TSI_LEVEL": -999,
            "CAIRPM2008_2.5_TSI_LEVEL": -999,
            "CAIRPM2008_10_TSI_LEVEL": -999,
            "CAIRPM2008_0.3_L_LEVEL": -999,
            "CAIRPM2008_0.5_L_LEVEL": -999,
            "CAIRPM2008_1.0_L_LEVEL": -999,
            "CAIRPM2008_2.5_L_LEVEL": -999,
            "CAIRPM2008_5_L_LEVEL": -999,
            "CAIRPM2008_10_L_LEVEL": -999
        }
    else:
        pm2008SensorVals = {}
        pm2008SensorVals["CAIRPM2008_1.0_GRIMM_LEVEL"] = 256*data[7]+data[8]
        pm2008SensorVals["CAIRPM2008_2.5_GRIMM_LEVEL"] = 256*data[9]+data[10]
        pm2008SensorVals["CAIRPM2008_10_GRIMM_LEVEL"] = 256*data[11]+data[12]
        pm2008SensorVals["CAIRPM2008_1.0_TSI_LEVEL"] = 256*data[13]+data[14]
        pm2008SensorVals["CAIRPM2008_2.5_TSI_LEVEL"] = 256*data[15]+data[16]
        pm2008SensorVals["CAIRPM2008_10_TSI_LEVEL"] = 256*data[17]+data[18]
        pm2008SensorVals["CAIRPM2008_0.3_L_LEVEL"] = 256*data[19]+data[20]
        pm2008SensorVals["CAIRPM2008_0.5_L_LEVEL"] = 256*data[21]+data[22]
        pm2008SensorVals["CAIRPM2008_1.0_L_LEVEL"] = 256*data[23]+data[24]
        pm2008SensorVals["CAIRPM2008_2.5_L_LEVEL"] = 256*data[25]+data[26]
        pm2008SensorVals["CAIRPM2008_5_L_LEVEL"] = 256*data[27]+data[28]
        pm2008SensorVals["CAIRPM2008_10_L_LEVEL"] = 256*data[29]+data[30]

    #return PM values
    return pm2008SensorVals

def ftc_mode(file):

    bus = init(0)
    data = read(bus)
    res = 0
    print('''1.0_TSI_LEVEL: %d ''' % data["CAIRPM2008_1.0_TSI_LEVEL"])
    print('''2.5_TSI_LEVEL: %d ''' % data["CAIRPM2008_2.5_TSI_LEVEL"])
    print('''10_TSI_LEVEL: %d ''' % data["CAIRPM2008_10_TSI_LEVEL"])

    output_json = {
        "serial_number": "null",
        "CAIRPM2008_1.0_TSI_LEVEL": str(data["CAIRPM2008_1.0_TSI_LEVEL"]),
        "CAIRPM2008_2.5_TSI_LEVEL": str(data["CAIRPM2008_2.5_TSI_LEVEL"]),
        "CAIRPM2008_10_TSI_LEVEL": str(data["CAIRPM2008_10_TSI_LEVEL"])
    }

    with open(file, 'w') as f:
        f.write(json.dumps(output_json))


    if  data["CAIRPM2008_1.0_TSI_LEVEL"] < data_upper_limit and data["CAIRPM2008_1.0_TSI_LEVEL"] > data_lower_limit and \
        data["CAIRPM2008_2.5_TSI_LEVEL"] < data_upper_limit and data["CAIRPM2008_1.0_TSI_LEVEL"] > data_lower_limit and \
        data["CAIRPM2008_10_TSI_LEVEL"] < data_upper_limit and data["CAIRPM2008_1.0_TSI_LEVEL"] > data_lower_limit      \
        :
        print("sensor value(s) are normal, OK")
        sys.exit(0)
    else:
        print("sensor value(s) are not within desired limits, FAIL")
        sys.exit(1)

def main():

    msg = "PM2008 Sensor Python Module"
    help_msg = "RUN_MODE options: normal ftc, default:normal"
    help_msg_output_file = "OUTPUT_FILE: specify file path to write serial number and the other data, default: /tmp/sensor_pm2008_out"

    parser = argparse.ArgumentParser(description=msg)

    parser.add_argument("-r", "--run_mode", type=str, default="normal", required=False, help = help_msg)      
    parser.add_argument("-o", "--output_file", type=str, default="/tmp/sensor_pm2008_out", required=False, help = help_msg_output_file)

    args = parser.parse_args()

    if args.run_mode == "ftc":
        ftc_mode(args.output_file)

    bus = init(0)
    pm2008_data = read(bus)
    
    
    return 0

if __name__ == '__main__':
    main()        
