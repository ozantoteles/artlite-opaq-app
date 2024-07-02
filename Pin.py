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
            call ("echo " + str(255) + " > /sys/class/leds/" + str(self.pin) + "/brightness",shell=True)
        else:
            call ("echo " + str(0) + " > /sys/class/leds/" + str(self.pin) + "/brightness",shell=True)
            
        log.info("Controlling Pin: %s Value: %s", str(self.pin), str(self.value))
    
    def on(self):
        self.setValue(0)
    
    def off(self):
        self.setValue(1)
        
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
