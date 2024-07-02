"""
Contains utlity functions and classes
"""

#!/usr/bin/python

import os
import logging
import logging.handlers
import sys
import shutil
from subprocess import call, check_output
import pickle

results_dir = "/tmp/cair-app/RESULTS/"
log_dir = "/tmp/cair-app/LOGS/"
log_file = log_dir + "log.txt"
variables_dir = "/home/cairapp/VARIABLES/"
voc_buffer_dir = "/home/cairapp/VOC"
nox_buffer_dir = "/home/cairapp/NOX"

def getFullPath(path):
    """
    :param path: path relative to project directory
    :return: absolute path to resource
    """
    return os.path.join(os.path.dirname(__file__), path)

def setUpLogger():
    """
    Sets up a logger that sends output to both the console and a file
    :return: logger object used to make calls
    """
    try:
        shutil.rmtree(log_dir)
    except Exception as e:
        logging.error(e)

    try:
        os.makedirs(log_dir) 
    except Exception as e:
        logging.error(e)

    logger = logging.getLogger('air_sampler')
    # Disable propagation of log messages to the root logger
    logger.propagate = False
    logger.setLevel(logging.DEBUG)
    format = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s - [%(pathname)s:%(lineno)d]')

    console = logging.StreamHandler(sys.stdout)
    console.setFormatter(format)
    logger.addHandler(console)

    fileHandler = logging.handlers.RotatingFileHandler(getFullPath(log_file))
    fileHandler.setFormatter(format)
    logger.addHandler(fileHandler)

    return logger

def write_variable(config_name, value):
    path = variables_dir + config_name + ".pkl"
    file_path = getFullPath(path)
    try:
        with open(file_path, 'wb') as file:
            pickle.dump(value, file, protocol = 2)
    except EOFError as e:
        logging.error(e)
        os.remove(file_path)
        return -1
    return 0
    
def read_variable(config_name):
    path = variables_dir + config_name + ".pkl"
    file_path = getFullPath(path)
    try:
        with open(file_path, 'rb') as file:
            data = pickle.load(file)
    except EOFError as e:
        logging.error(e)
        os.remove(file_path)
        return -1
    return data
    
def check_if_file_exist(full_path):
    return os.path.exists(full_path)

def set_wl_country_code(ccode="TR"):
    call(["/usr/sbin/wl", "country", str(ccode)]);

def get_wl_country_code():
    command = "wl country | awk {print'$1'}"
    value = check_output(command, shell=True).rstrip()
    return value

class PumpConfig:
    def __init__(self, data):
        self.pin = data['cntrlPin']
        self.enable = data['enablePin']
        self.runTime = data['runTime']
        self.level = data['fanLevel']

class LazerConfig:
    def __init__(self, data):
        self.pin = data['cntrlPin']
        self.level = data['laserLevel']

class ButtonConfig:
    def __init__(self, data):
        self.pin = data['pin']

class CameraController:
    def __init__(self, data):
        self.exposure = data['exposure']
        self.usb = data['usb']
        self.power_pin = data['power_pin']
        self.powerOff()

    def setExposure(self):
        # set exposure_auto value
        retval = call(["/usr/bin/v4l2-ctl", "-d", "/dev/video1", "-c", "auto_exposure=1"])
        if retval != 0:
            return retval

        # set exposure_absolute value
        retval = call(["/usr/bin/v4l2-ctl", "-d", "/dev/video1", "-c", "exposure_time_absolute="+str(self.exposure)])
        if retval != 0:
            return retval
        return retval

    def getExposure(self):
        command = "echo $(v4l2-ctl -d /dev/video1 -C exposure_time_absolute) | sed -e 's/[: ]/_/g'"
        value = check_output(command, shell=True).rstrip()
        return value.decode('utf-8')
    
    def powerOn(self):
        call ("echo 0" + " > /sys/bus/usb/devices/" + self.usb + "/authorized",shell=True)
        call ("echo 1" + " > /sys/class/leds/" + self.power_pin + "/brightness",shell=True)
        call ("echo 1" + " > /sys/bus/usb/devices/" + self.usb + "/authorized",shell=True)
    
    def powerOff(self):
        call ("echo 0" + " > /sys/class/leds/" + self.power_pin + "/brightness",shell=True)
