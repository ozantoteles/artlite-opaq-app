import time
import argparse
import json
import sys
from sensirion_i2c_driver import LinuxI2cTransceiver, I2cConnection
from sensirion_i2c_sht.sht4x.device import Sht4xI2cDevice
from sensirion_i2c_sht.sht3x.device import Sht3xI2cDevice
sys.path.insert(0, "/usr/local/cair-app/")
from config import log


# Define I2C address constants for RHT sensors
SHT40_BD1B_ADDR = 0x45 # SHT40-BD1B base RH&T accur., 0x45 I2C addr., c-Air Sensor Baseboard onboard RHT sensor
Z7N904R_SHT30_ADDR = 0x44 # Z7N904R SHT30 Module, c-Air external RHT Sensor

SHT_BUS_NO = 0

# Define upper and lower limits for temperature and humidity data (for FTC mode)
TEMP_DATA_UPPER_LIMIT = 125
TEMP_DATA_LOWER_LIMIT = -40
HUM_DATA_UPPER_LIMIT = 100
HUM_DATA_LOWER_LIMIT = 0


    
def init(busNo, sensorName, addr=Z7N904R_SHT30_ADDR): 
    busNo_addr = '/dev/i2c-'+ str(busNo)
    i2c_transceiver_sht = LinuxI2cTransceiver(busNo_addr)
    try:
        if addr == SHT40_BD1B_ADDR:
            sht = Sht4xI2cDevice(I2cConnection(i2c_transceiver_sht), slave_address=addr)
        elif addr == Z7N904R_SHT30_ADDR:
            sht = Sht3xI2cDevice(I2cConnection(i2c_transceiver_sht), slave_address=addr)
    except:
        log.error("Error initializing %s.", sensorName)
        i2c_transceiver_sht.close()
        return -1, -1  
    
    log.debug("%s initialized successfully.", sensorName)
    
    return sht, i2c_transceiver_sht
    
    
def read(sensor, i2cTransceiver):
    
    temperature, humidity = sensor.single_shot_measurement()
    
    log.debug('SHT Temperature ticks: %d', temperature.ticks)
    log.debug('SHT Temperature celcius: %f', temperature.degrees_celsius)
    log.debug('SHT Temperature fahrenheit: %f', temperature.degrees_fahrenheit)
    log.debug('SHT Relative Humidity ticks: %d', humidity.ticks)
    log.debug('SHT Relative Humidity RH: %f', humidity.percent_rh)
    
    sht_data = {}
    temp = temperature.degrees_celsius
    hum = humidity.percent_rh
    i2cTransceiver.close()
    return temp, hum

def ftc_mode(sensor_type="internal", file="/tmp/sensor_rht_out"):
    if sensor_type == "internal":
        addr = SHT40_BD1B_ADDR
    else:
        addr = Z7N904R_SHT30_ADDR

    bus, i2c_transceiver_sht = init(SHT_BUS_NO, "SHT", addr)
    temp, hum = read(bus, i2c_transceiver_sht)
    print('''Temperature: %d ''' % temp)
    print('''Rel. Humidity: %d ''' % hum)

    output_json = {
        "serial_number": "null",
        "sensor_temp": str(temp),
        "sensor_hum": str(hum)
    }

    with open(file, 'w') as f:
        f.write(json.dumps(output_json))


    if  temp < TEMP_DATA_UPPER_LIMIT and temp > TEMP_DATA_LOWER_LIMIT and   \
        hum < HUM_DATA_UPPER_LIMIT and hum > HUM_DATA_LOWER_LIMIT           \
        :
        print("sensor value(s) are normal, OK")
        sys.exit(0)
    else:
        print("sensor value(s) are not within desired limits, FAIL")
        sys.exit(1)
    
def main():
    # FTC
    msg = "RHT Sensor Python Module"
    help_msg_run_mode = "RUN_MODE options: normal ftc, default:normal"
    help_msg_sensor_select = "SENSOR_SELECT options: internal external, default:internal"
    help_msg_output_file = "OUTPUT_FILE: specify file path to write serial number and the other data, default: /tmp/sensor_rht_out"

    parser = argparse.ArgumentParser(description=msg)

    parser.add_argument("-r", "--run_mode", type=str, default="normal", required=False, help = help_msg_run_mode)
    parser.add_argument("-s", "--sensor_select", type=str, default="internal", required=False, help = help_msg_sensor_select)
    parser.add_argument("-o", "--output_file", type=str, default="/tmp/sensor_rht_out", required=False, help = help_msg_output_file)        

    args = parser.parse_args()
 
    if args.run_mode == "ftc":
        
        if args.sensor_select != "internal" and args.sensor_select != "external":
            print("invalid sensor select option!")
            sys.exit(1)
        else:
            ftc_mode(args.sensor_select, args.output_file)            
    # Sensor init and read
    try:
        sht, i2c_transceiver_sht = init(SHT_BUS_NO, "SHT", Z7N904R_SHT30_ADDR)
        # sht = init(SHT_BUS_NO, Z7N904R_SHT30_ADDR)
        temp, hum = read(sht, i2c_transceiver_sht)
        
        # Log the temp, hum, hcho values, and device marking
        log.info('SHT Temperature: %f', temp)
        log.info('SHT Relative Humidity: %f', hum)

    except Exception as e:
        # Log any exceptions
        log.error('An error occurred: %s', str(e))

    return 0

if __name__ == '__main__':
    main()