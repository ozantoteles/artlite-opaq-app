#!/usr/bin/python

import time
from subprocess import call
from subprocess import check_output
from config import log 

class Pin:
    def __init__(self, pin, value=0):
        self.pin = pin
        self.setValue(value)

    def setValue(self, value):
        self.value = value
        if self.value:
            if self.pin == "lazer_cntrl":
                call ("echo " + str(4096) + " > /sys/class/leds/" + str(self.pin) + "/brightness",shell=True)
            elif self.pin == "red_cntrl" or self.pin == "green_cntrl":
                call ("echo " + str(255) + " > /sys/class/leds/" + str(self.pin) + "/brightness",shell=True)
            else: #usb2_en
                call ("echo " + str(1) + " > /sys/class/leds/" + str(self.pin) + "/brightness",shell=True)
        else:
            call ("echo " + str(0) + " > /sys/class/leds/" + str(self.pin) + "/brightness",shell=True)
            
        #log.info("Controlling Pin: %s Value: %s", str(self.pin), str(self.value))
        print("Controlling Pin: ",str(self.pin), " Value: ",str(self.value))
    
    
    def on(self):
        self.setValue(1)
    
    def off(self):
        self.setValue(0)
        
    def getValue(self):
        return self.value

    def toggle(self, delay):
        self.setValue(1)
        time.sleep(delay)
        self.setValue(0)
        time.sleep(delay)

class Button:
    def __init__(self, pin):
        self.pin = pin

    def getValue(self):
        command = "cat /sys/class/leds/" + str(self.pin) + "/brightness"
        val = check_output(command, shell=True)
        return val
