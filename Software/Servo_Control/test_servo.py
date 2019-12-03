#!/usr/bin/python3

import serial
import datetime
import time

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
 
    time.sleep(0.005)  #delay

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

# def get_high_low_bytes(input_number):

#     high_byte = input_number>>8
#     low_byte = input_number & 0xFF

#     return high_byte, low_byte

# servoWriteCmd(1, command["LOAD_UNLOAD_WRITE"],0)  #turn motor off, make servo turnable by hand

# for ind in range(0,1000,100):
#     time.sleep(5)
#     servoWriteCmd(1,command["MOVE_WRITE"],ind,2000)                                                                                                                                                                                                               
#     print((ind,readPosition(1)))

joint_id = {
"joint_1" : 5,
"joint_2" : 1,
"joint_3" : 2,
"joint_4" : 4,
"joint_5" : 6,
"joint_6" : 3
}

for ind in range(1,7):
    servoWriteCmd(ind,command["SERVO_MODE_WRITE"],0)
    servoWriteCmd(ind, command["LOAD_UNLOAD_WRITE"],0)  #turn motor off, make servo turnable by hand

while True:
    angle_out = []
    tem_out = []
    for key in joint_id.keys():
        angle_out.append(readPosition(joint_id[key]))
        tem_out.append(readTemperature(joint_id[key]))
    
    print(angle_out)
    print(tem_out)

