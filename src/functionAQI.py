import json

def getQuality(json_file="AQI.json", dataPM1_0=-1, dataRH_humid=-1, dataCO=-1, dataNO2=-1, dataCO2=-1, dataVOC=-1, dataPM10=-1, dataRH_dry=-1, dataPM2_5=-1, return_json=False):
    
    index_dictionary = {} # keeps index values of all parameters plus total index as dictionary then it is returned as json object
    normalized_values = [] # keeps all normalized index values for the given value as well as the corresponding quality info
    
    with open(json_file, "r") as f:
        data = json.load(f) # returns JSON object as a dictionary   
    key_value_dict = {
        'CO2 (ppm)': dataCO2,
        'PM1.0 (ug/m3)': dataPM1_0,
        'PM2.5 (ug/m3)': dataPM2_5,
        'PM10 (ug/m3)': dataPM10,
        'RH(%) DRY': dataRH_dry,
        'RH(%) HUMID': dataRH_humid,
        'VOC (Sensirion Index)': dataVOC,
        'CO*': dataCO,
        'NO2*': dataNO2 
    }

    for key in data.keys():
        
        if ( key!="Quality" and key!="Index"):
            value = key_value_dict[key]
            
            for idx in data[key].keys():
                min_max_range = data[key][idx].split("-")
                
                if (value < float(min_max_range[1])) & (value >= float(min_max_range[0])):
                    index = data["Index"][idx].split("-") 
                    
                    normalized_value = float(index[0]) + (((value - float(min_max_range[0]))/(float(min_max_range[1])-float(min_max_range[0])))*(float(index[1])-float(index[0])))
                    normalized_values.append([round(normalized_value,1),data["Quality"][idx]])

                    index_dictionary[key] = {}
                    index_dictionary[key]["Index"] = round(normalized_value,1) 
                    index_dictionary[key]["Level"] = data["Quality"][idx]
                    break
 
    index_value = -1
    quality = "error"

    for value in normalized_values: # max index value(total index) is found 
        
        if(value[0] > index_value):
            index_value = value[0]
            quality = value[1]

    index_dictionary["Total Index"] = {}  # adding new key with total index value       
    index_dictionary["Total Index"]["Index"] = index_value 
    index_dictionary["Total Index"]["Level"] = quality

    if return_json == False:
        return index_value,quality
    else:
        return json.dumps(index_dictionary) # json.dumps() function converts a Python object into a json string
