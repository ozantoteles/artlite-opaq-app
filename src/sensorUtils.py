#!/usr/bin/python
import drivers.driver_co2 as sensorCO2
import drivers.driver_pm as sensorPM2008
import drivers.driver_sht as sensorRHT
import drivers.driver_sgp4x as sensorTVOC2
import drivers.driver_adcs as sensorADCs
import batteryController
from functionAQI import getQuality

busNR_CM1107 = 0
busNR_PM2008 = 0
busNR_RHT = 0
busNR_TVOC = 0
busNR_BAT = 0

# Define I2C address constants for RHT sensors
SHT40_BD1B_ADDR = 0x45 # SHT40-BD1B base RH&T accur., 0x45 I2C addr., c-Air Sensor Baseboard onboard RHT sensor
Z7N904R_SHT30_ADDR = 0x44 # Z7N904R SHT30 Module, c-Air external RHT Sensor

#default adc paths for cair
adcPATH_CO  = '/sys/bus/iio/devices/iio:device0/in_voltage0_raw'
adcPATH_NH3 = '/sys/bus/iio/devices/iio:device0/in_voltage6_raw'
adcPATH_NO2 = '/sys/bus/iio/devices/iio:device0/in_voltage8_raw'


class SensorHandler:
    def __init__(self):
        self.sensorData = {}
        self.batData = {}
        self.__is_battery_controller_busy = False
        
    def init_sensor(self, sensor, busNo, sensorName, sensorModel = None, conditioning = False, addr = None):
        if sensorModel != None: # SGP4X
            sensorBus, i2cTransceiver = sensor.init(busNo, sensorName, sensorModel = sensorModel, conditioning = conditioning)
            return sensorBus, i2cTransceiver
                
        elif addr != None: # SHT
            sensorBus, i2cTransceiver = sensor.init(busNo, sensorName, addr = addr)
            return sensorBus, i2cTransceiver
        
        else: # CO2, PM, BAT
            try:
                sensorBus = sensor.init(busNo)
                print('%s initialized successfully.',sensorName)
                return sensorBus
            except Exception as e:
                print('Error initializing %s: %s',sensorName,e)
                return -1
   
    def read_sensor(self, sensor, sensorBus, sensorName, i2cTransceiver = None, sensorModel = None, temp = None, hum = None):    
        if i2cTransceiver != None and sensorModel != None: # SGP
            try:
                data = sensor.read(sensorBus, i2cTransceiver = i2cTransceiver , sensorModel = sensorModel, temperature = temp, humidity = hum) 
                return data
            except Exception as e:
                i2cTransceiver.close()
                print('Error reading %s: %s',sensorName,e)
                return -999
                
        elif i2cTransceiver != None and sensorModel == None: # SHT
            try:
                data = sensor.read(sensorBus, i2cTransceiver = i2cTransceiver)                          
                return data
            except Exception as e:
                i2cTransceiver.close()
                print('Error reading %s: %s',sensorName,e)
                return -999
                
        else: # CO2, PM, BAT
            try:
                data = sensor.read(sensorBus) 
                return data
            except Exception as e:
                print('Error reading %s: %s',sensorName,e)
                return -999
                
    def handler(self):
    
        dataCO2 = -999
        dataPM2008 = -999
        dataRHT = -999
        dataSGP4x = -999
        dataRHT_External_Hum = -999
        dataRHT_External_Temp = -999
        dataTVOC_VOC = -999
        dataCO = -999
        dataNH3 = -999
        dataNO2 = -999
        
        self.sensorData['CAIRRHTLEVEL_EXTERNAL_TEMP'] = -999
        self.sensorData['CAIRRHTLEVEL_EXTERNAL_HUM'] = -999
        
        self.sensorData['CAIRTVOCLEVEL'] = -999
        self.sensorData['CAIRNO2LEVEL'] = -999
            
        self.sensorData["CAIRPM2008_1.0_TSI_LEVEL"] = -999
        self.sensorData["CAIRPM2008_2.5_TSI_LEVEL"] = -999
        self.sensorData["CAIRPM2008_10_TSI_LEVEL"] = -999
        
        # unused pm2008 data
        self.sensorData["CAIRPM2008_0.3_L_LEVEL"] = -999
        self.sensorData["CAIRPM2008_0.5_L_LEVEL"] = -999
        self.sensorData["CAIRPM2008_1.0_GRIMM_LEVEL"] = -999
        self.sensorData["CAIRPM2008_1.0_L_LEVEL"] = -999
        self.sensorData["CAIRPM2008_2.5_GRIMM_LEVEL"] = -999
        self.sensorData["CAIRPM2008_2.5_L_LEVEL"] = -999
        self.sensorData["CAIRPM2008_5_L_LEVEL"] = -999
        self.sensorData["CAIRPM2008_10_GRIMM_LEVEL"] = -999
        self.sensorData["CAIRPM2008_10_L_LEVEL"] = -999

        self.sensorData["CAIRCOLEVEL"] = -999
        
        dataBAT = -999
        dataBATState = -999
        
        # CO2
        self.busCM1107 = self.init_sensor(sensorCO2, busNR_CM1107 , 'CM1107')
        if self.busCM1107 != -1:
            dataCO2 = self.read_sensor(sensorCO2, self.busCM1107, 'CM1107')
            print('dataCO2: %s',dataCO2)

            
        # PM
        self.busPM2008 = self.init_sensor(sensorPM2008, busNR_PM2008, 'PM2008') 
        if self.busPM2008 != -1:
            dataPM2008 = self.read_sensor(sensorPM2008, self.busPM2008, 'PM2008')
            print('dataPM2008: %s',dataPM2008)
      

        # RHT
        self.busRHText, self.i2cTransceiver_sht = self.init_sensor(sensorRHT, busNR_RHT, 'SHT30', addr = Z7N904R_SHT30_ADDR) 
        if self.busRHText != -1 and self.i2cTransceiver_sht != -1:
            dataRHT = self.read_sensor(sensorRHT, self.busRHText, 'SHT30', i2cTransceiver = self.i2cTransceiver_sht)
            print('dataRHT: %s',dataRHT)
        

        # RHT + VOC
        self.busRHT, self.i2cTransceiver_sht40 = self.init_sensor(sensorRHT, busNR_RHT, 'SHT40', addr = SHT40_BD1B_ADDR) 
        if self.busRHT != -1 and self.i2cTransceiver_sht40 != -1:
            dataRHT_internal = self.read_sensor(sensorRHT, self.busRHT, 'SHT40', i2cTransceiver = self.i2cTransceiver_sht40)
            if dataRHT_internal != -999:
                temp_voc, hum_voc = dataRHT_internal[0], dataRHT_internal[1]
                print("Temp on board: %f", temp_voc)
                print("Hum on board: %f", hum_voc)
                print("Temperature and humidity data for voc are obtained from onboard sensors")
            else:
                if dataRHT != -999:
                    temp_voc, hum_voc = dataRHT[0], dataRHT[1]
                    print("Temp external: %f", temp_voc)
                    print("Hum external: %f", hum_voc)
                    print("Temperature and humidity data for voc are obtained from external sensors")
                else:
                    temp_voc, hum_voc = 25, 50
                    print("Temp external: %f", temp_voc)
                    print("Hum external: %f", hum_voc)
                    print("Temperature and humidity data for voc are set to default values")
        else:
            if dataRHT != -999:
                temp_voc, hum_voc = dataRHT[0], dataRHT[1]
                print("Temp external: %f", temp_voc)
                print("Hum external: %f", hum_voc)
                print("Temperature and humidity data for voc are obtained from external sensors")
            else:
                temp_voc, hum_voc = 25, 50
                print("Temp external: %f", temp_voc)
                print("Hum external: %f", hum_voc)
                print("Temperature and humidity data for voc are set to default values")
        
        self.busTVOC, self.i2cTransceiver_sgp = self.init_sensor(sensorTVOC2, busNR_TVOC, 'SGP41', sensorModel = 'SGP41', conditioning=False) 
        if self.busTVOC != -1 and self.i2cTransceiver_sgp != -1:
            dataSGP4x = self.read_sensor(sensorTVOC2, self.busTVOC, 'SGP41', i2cTransceiver = self.i2cTransceiver_sgp, sensorModel =  'SGP41', temp = temp_voc, hum = hum_voc)
            print('dataSGP4x: %s',dataSGP4x)
            
        
        # Battery
        while self.__is_battery_controller_busy:
            pass
        self.__is_battery_controller_busy = True
        self.busBAT = self.init_sensor(batteryController, busNR_BAT, 'Battery')
        if self.busBAT != -1:
            resp_read_battery = self.read_sensor(batteryController, self.busBAT, 'Battery')
            self.__is_battery_controller_busy = False
            if resp_read_battery != -999:
                dataBAT, dataBATState = resp_read_battery[0], resp_read_battery[1]
                print('dataBAT: %s',dataBAT)
                print('dataBATState: %s',dataBATState)



        self.sensorData['CAIRCO2LEVEL'] = dataCO2
        self.sensorData["STT_BATTERY_LEVEL"] = dataBAT
        self.sensorData["STT_CAIR_BATTERY_STATUS"] = dataBATState
        
        if dataRHT != -999:
            self.sensorData['CAIRRHTLEVEL_EXTERNAL_TEMP'] = dataRHT[0]
            self.sensorData['CAIRRHTLEVEL_EXTERNAL_HUM'] = dataRHT[1]
            
        if dataSGP4x != -999 :   
            self.sensorData['CAIRTVOCLEVEL'] = dataSGP4x[0]
            self.sensorData['CAIRNO2LEVEL'] = dataSGP4x[1]
          
        if dataPM2008 != -999:
            self.sensorData['CAIRPM2008_1.0_TSI_LEVEL'] = dataPM2008['CAIRPM2008_1.0_TSI_LEVEL']
            self.sensorData['CAIRPM2008_2.5_TSI_LEVEL'] = dataPM2008['CAIRPM2008_2.5_TSI_LEVEL']
            self.sensorData['CAIRPM2008_10_TSI_LEVEL'] = dataPM2008['CAIRPM2008_10_TSI_LEVEL']
            
            self.sensorData['CAIRPM2008_0.3_L_LEVEL'] = dataPM2008['CAIRPM2008_0.3_L_LEVEL']
            self.sensorData['CAIRPM2008_0.5_L_LEVEL'] = dataPM2008['CAIRPM2008_0.5_L_LEVEL'] 
            self.sensorData['CAIRPM2008_1.0_GRIMM_LEVEL'] = dataPM2008['CAIRPM2008_1.0_GRIMM_LEVEL']
            self.sensorData['CAIRPM2008_1.0_L_LEVEL'] = dataPM2008['CAIRPM2008_1.0_L_LEVEL']
            self.sensorData['CAIRPM2008_2.5_GRIMM_LEVEL'] = dataPM2008['CAIRPM2008_2.5_GRIMM_LEVEL']
            self.sensorData['CAIRPM2008_2.5_L_LEVEL'] = dataPM2008['CAIRPM2008_2.5_L_LEVEL']
            self.sensorData['CAIRPM2008_5_L_LEVEL'] = dataPM2008['CAIRPM2008_5_L_LEVEL']
            self.sensorData['CAIRPM2008_10_GRIMM_LEVEL'] = dataPM2008['CAIRPM2008_10_GRIMM_LEVEL']
            self.sensorData['CAIRPM2008_10_L_LEVEL'] = dataPM2008['CAIRPM2008_10_L_LEVEL']

        return self.sensorData 
    
    
    def read_battery_controller(self): 
        # Battery
        dataBAT = -999
        dataBATState = -999
        import time
        
        while self.__is_battery_controller_busy:
            time.sleep(0.1)  # Sleep briefly to release the CPU
        self.__is_battery_controller_busy = True
        self.busBAT = self.init_sensor(batteryController, busNR_BAT, 'Battery')
        if self.busBAT != -1:
            resp_read_battery = self.read_sensor(batteryController, self.busBAT, 'Battery')
            self.__is_battery_controller_busy = False
            if resp_read_battery != -999:
                dataBAT, dataBATState = resp_read_battery[0], resp_read_battery[1]
                print('dataBAT: %s',dataBAT)
                print('dataBATState: %s',dataBATState)
        
        self.batData['STT_BATTERY_LEVEL'] = dataBAT
        self.batData['STT_CAIR_BATTERY_STATUS'] = dataBATState        
        
        return self.batData 
        
def main():
    sensor_object = SensorHandler() 
    #while(1):
    try:
        sensor_data = sensor_object.handler()
        print('Measurements: %s',sensor_data)
    except Exception as e:
        print('An error occurred: %s',e)

if __name__ == '__main__':
    main()
