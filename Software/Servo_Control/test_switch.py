#!/usr/bin/python3

import serial
import datetime
import time
import csv
import RPi.GPIO as GPIO

GPIO.setmode(GPIO.BCM)
GPIO.setup(5,GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

i = 0
while True:
    if not GPIO.input(5):
        print('low '+str(i))
        i += 1