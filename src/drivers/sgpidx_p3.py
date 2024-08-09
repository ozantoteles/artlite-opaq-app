from sensirion_gas_index_algorithm.voc_algorithm import VocAlgorithm
from sensirion_gas_index_algorithm.nox_algorithm import NoxAlgorithm
import csv, sys, os

measurement_type = sys.argv[1] 
measurement = sys.argv[2] 
bufferSize = int(sys.argv[3] )
bufferFolder = sys.argv[4] 
bufferFile = sys.argv[5] 

if not os.path.exists(bufferFolder):
    os.makedirs(bufferFolder)

with open(bufferFile, 'a+', newline='') as f: 
    reader = csv.reader(f)
    lenofraw=len(list(reader))
    
if lenofraw < bufferSize:
    with open(bufferFile, 'a+', newline='') as fin:
        writer = csv.writer(fin)
        writer.writerow([measurement])
else:
    with open(bufferFile, 'r') as fd:
        data = fd.read().splitlines(True)
    with open(bufferFile, 'w') as fout:
        fout.writelines(data[1:])
    with open(bufferFile, 'a+', newline='') as fin:
        writer = csv.writer(fin)
        writer.writerow([measurement])

with open(bufferFile, 'r') as fin:
    rawarray = fin.read().splitlines(True)

if measurement_type == "VOC":
    voc_algorithm = VocAlgorithm()
    for rawdata in rawarray:
        voc_index = voc_algorithm.process(int(rawdata))
    print(voc_index)
    
elif measurement_type == "NOX":
    nox_algorithm = NoxAlgorithm()
    for rawdata in rawarray:
        nox_index = nox_algorithm.process(int(rawdata))
    print(nox_index)

