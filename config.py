#!/usr/bin/python
import configUtils as utils

JSON_MSG = {
    "pump": {
        "runTime": 10, 
        "fanLevel": 180, 
        "enablePin": "fan_on", 
        "cntrlPin": "fan_cntrl"
        }, 
    "lazer": {
        "laserLevel": 4096, 
        "cntrlPin": "lazer_cntrl"
        }, 
    "camera_controller": {
        "power_pin": "usb2_en",
        "usb": "usb2",
        "exposure": 2000
        }
}

log = utils.setUpLogger()
camera_controller = utils.CameraController(JSON_MSG['camera_controller'])
pump = utils.PumpConfig(JSON_MSG['pump'])
lazer = utils.LazerConfig(JSON_MSG['lazer'])
