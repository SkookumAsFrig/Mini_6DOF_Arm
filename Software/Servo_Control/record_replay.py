#!/usr/bin/python3

import serial
import datetime
import time


serialHandle = serial.Serial("/dev/ttyUSB0", 115200)  #115200 baud rate

command = {"MOVE_WRITE":1, "POS_READ":28, "SERVO_MODE_WRITE":29,"LOAD_UNLOAD_WRITE": 31,"SERVO_MOVE_STOP":12}

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
 
    time.sleep(0.01)  #delay

    count = serialHandle.inWaiting() #get number of bytes in serial buffer
    pos = None
    if count != 0: #if not empty
        recv_data = serialHandle.read(count) #read data
        if count == 8: #if it matches expected data length
            if recv_data[0] == 0x55 and recv_data[1] == 0x55 and recv_data[4] == 0x1C :
                #first and second bytes are 0x55, fifth byte is 0x1C (28), which is read position command
                 pos= 0xffff & (recv_data[5] | (0xff00 & (recv_data[6] << 8))) #combine data for valid read
                 
    return pos

# def get_high_low_bytes(input_number):

#     high_byte = input_number>>8
#     low_byte = input_number & 0xFF

#     return high_byte, low_byte

# servoWriteCmd(1, command["LOAD_UNLOAD_WRITE"],0)  #turn motor off, make servo turnable by hand

# for ind in range(0,1000,100):
#     time.sleep(5)
#     servoWriteCmd(1,command["MOVE_WRITE"],ind,2000)                                                                                                                                                                                                               
#     print((ind,readPosition(1)))

joint_id = { #[real servo id, home position]
"joint_1" : [5, 852],
"joint_2" : [1, 597],
"joint_3" : [2, 135],
"joint_4" : [4, 510],
"joint_5" : [6, 900],
"joint_6" : [3, 474]
}


for key in joint_id.keys():
    if key != "joint_6":
        servoWriteCmd(joint_id[key][0],command["MOVE_WRITE"],joint_id[key][1],0)
    else:
        servoWriteCmd(joint_id[key][0], command["LOAD_UNLOAD_WRITE"],0)  #turn motor off, make servo turnable by hand

togg = True
tog_speed = 1000
times = 0

while True:
    if tog_speed>=150:
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
    else:
        servoWriteCmd(joint_id["joint_6"][0],command["SERVO_MODE_WRITE"],1,0)

    time.sleep(0.05)

    angle_out = []
    for key in joint_id.keys():
        angle_out.append(readPosition(joint_id[key][0]))
    
    print(angle_out)
