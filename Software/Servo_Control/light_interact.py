#!/usr/bin/python3

import serial
import datetime
import time
import csv
import RPi.GPIO as GPIO
from threading import Thread

GPIO.setmode(GPIO.BCM)
GPIO.setup(5,GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

global joint_id
global command
global off_mode
global light_on_sw
light_on_sw = False
off_mode = True

joint_id = { #[real servo id, home position]
"joint_1" : [5, 852],
"joint_2" : [1, 597],
"joint_3" : [2, 135],
"joint_4" : [4, 510],
"joint_5" : [6, 900],
"joint_6" : [3, 474]
}

def GPIO5cb():
    global light_on_sw
    global joint_id
    global command
    global off_mode
    while True:
        time.sleep(0.1)
        if light_on_sw:

            if off_mode:
                off_file = 'light_off.csv'
            else:
                off_file = 'light_off2.csv'

            off_mode = not off_mode

            for key in joint_id.keys():
                servoWriteCmd(joint_id[key][0],command["SERVO_MODE_WRITE"],0)
                servoWriteCmd(joint_id[key][0],command["MOVE_WRITE"],joint_id[key][1],0)

            time.sleep(1.5)

            init_time = time.time()
            duration = 0

            with open(off_file) as csvfile:
                pamreader = csv.reader(csvfile,delimiter=',')
                for row in pamreader:
                    duration = time.time() - init_time
                    try:
                        newrow = list(map(float,row))
                    except Exception as e:
                        continue
                        # print(row)
                    rec_time = newrow[-1]
                    while(duration<rec_time):
                        duration = time.time() - init_time
                        time.sleep(0.0000001)
                    
                    ind = 0
                    for key in joint_id.keys():
                        servoWriteCmd(joint_id[key][0],command["MOVE_WRITE"],int(newrow[ind]),0)
                        ind += 1
            
            togg = True
            tog_speed = 1000
            times = 0

            while tog_speed>=150:
                time.sleep(0.03)
                if togg:
                    servoWriteCmd(joint_id["joint_6"][0],command["SERVO_MODE_WRITE"],1,tog_speed)
                else:
                    servoWriteCmd(joint_id["joint_6"][0],command["SERVO_MODE_WRITE"],1,-tog_speed)
                togg = not togg
                if times<2:
                    times += 1
                else:
                    tog_speed -= 150
                    times = 0

            light_on_sw = False

            servoWriteCmd(joint_id["joint_6"][0],command["SERVO_MODE_WRITE"],1,0)
            servoWriteCmd(joint_id["joint_6"][0],command["SERVO_MODE_WRITE"],0)

light_off_thread = Thread(target=GPIO5cb,daemon=True)
light_off_thread.daemon = True
light_off_thread.start()

serialHandle = serial.Serial("/dev/ttyUSB0", 115200)  #115200 baud rate

command = {"MOVE_WRITE":1, "POS_READ":28, "SERVO_MODE_WRITE":29,
"LOAD_UNLOAD_WRITE": 31,"SERVO_MOVE_STOP":12, "TEMP_READ": 26}

#No need to split into higher and lower bytes, this function does it already. Parameter # is # of different params.
def servoWriteCmd(id, cmd, par1 = None, par2 = None):
    buf = bytearray(b'\x55\x55')
    try:
        len = 3   #length is 3 if no commands
        buf1 = bytearray(b'')

	## verify data
        if par1 is not None:
            len += 2  #add 2 to data length
            buf1.extend([(0xff & par1), (0xff & (par1 >> 8))])  #split into lower and higher bytes, store in buffer
        if par2 is not None:
            len += 2
            buf1.extend([(0xff & par2), (0xff & (par2 >> 8))])  #split into lower and higher bytes, store in buffer
        buf.extend([(0xff & id), (0xff & len), (0xff & cmd)])
        buf.extend(buf1)

	## checksum
        sum = 0x00
        for b in buf:  #sum
            sum += b
        sum = sum - 0x55 - 0x55  #remove two beginning 0x55
        sum = ~sum  #take not
        buf.append(0xff & sum)  #add lower byte into buffer
        serialHandle.write(buf) #send
    except Exception as e:
        print(e)

def readPosition(id):
 
    serialHandle.flushInput()
    servoWriteCmd(id, command["POS_READ"]) #send read command
 
    time.sleep(0.0055)  #delay

    count = serialHandle.inWaiting() #get number of bytes in serial buffer
    pos = None
    if count != 0: #if not empty
        recv_data = serialHandle.read(count) #read data
        if count == 8: #if it matches expected data length
            if recv_data[0] == 0x55 and recv_data[1] == 0x55 and recv_data[4] == 0x1C :
                #first and second bytes are 0x55, fifth byte is 0x1C (28), which is read position command
                 pos= 0xffff & (recv_data[5] | (0xff00 & (recv_data[6] << 8))) #combine data for valid read
                 
    return pos

def readTemperature(id):
 
    serialHandle.flushInput()
    servoWriteCmd(id, command["TEMP_READ"]) #send read command
 
    time.sleep(0.01)  #delay

    count = serialHandle.inWaiting() #get number of bytes in serial buffer
    tem = None
    if count != 0: #if not empty
        recv_data = serialHandle.read(count) #read data
        if count == 7: #if it matches expected data length
            if recv_data[0] == 0x55 and recv_data[1] == 0x55 and recv_data[4] == 0x1A :
                #first and second bytes are 0x55, fifth byte is 0x1A (26), which is read temperature command
                 tem = recv_data[5]
                 
    return tem

cont_var = 0
last_input = True

while True:
    time.sleep(0.5)
    now_input = GPIO.input(5)
    if not now_input and not last_input:
        cont_var += 1
    else:
        cont_var = 0

    if cont_var>6:
        cont_var = -10
        light_on_sw = True

    # print(cont_var)
    
    last_input = now_input