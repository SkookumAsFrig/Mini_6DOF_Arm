#!/usr/bin/python3

import serial
import time


serialHandle = serial.Serial("/dev/ttyUSB0", 115200)  #115200 baud rate

command = {"MOVE_WRITE":1, "POS_READ":28, "SERVO_MODE_WRITE":29,
"LOAD_UNLOAD_WRITE": 31,"SERVO_MOVE_STOP":12, "TEMP_READ": 26, "ID_READ": 14}

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


def readID(id):
 
    serialHandle.flushInput()
    servoWriteCmd(id, command["ID_READ"]) #send read command
 
    time.sleep(0.0055)  #delay

    count = serialHandle.inWaiting() #get number of bytes in serial buffer
    servid = None
    if count != 0: #if not empty
        recv_data = serialHandle.read(count) #read data
        if count == 7: #if it matches expected data length
            if recv_data[0] == 0x55 and recv_data[1] == 0x55 and recv_data[4] == 0x10 :
                #first and second bytes are 0x55, fifth byte is 0x10 (14), which is read id command
                 servid= recv_data[5]
                 
    return servid

def readTemperature(id):
 
    serialHandle.flushInput()
    servoWriteCmd(id, command["TEMP_READ"]) #send read command
 
    time.sleep(0.0055)  #delay

    count = serialHandle.inWaiting() #get number of bytes in serial buffer
    tem = None
    if count != 0: #if not empty
        recv_data = serialHandle.read(count) #read data
        if count == 7: #if it matches expected data length
            if recv_data[0] == 0x55 and recv_data[1] == 0x55 and recv_data[4] == 0x1A :
                #first and second bytes are 0x55, fifth byte is 0x1A (26), which is read temperature command
                 tem = recv_data[5]
                 
    return tem

joint_id = { #[real servo id, command position]
"joint_1" : [1, 852]
}

servoWriteCmd(joint_id["joint_1"][0], command["LOAD_UNLOAD_WRITE"],0)

while True:
    pos = readPosition(joint_id["joint_1"][0])
    # temp = readTemperature(joint_id["joint_1"][0])
    # servo_id = readID(0xFE)
    # if temp is None:
    #     temp = 'temp is NoneType'
    if pos is None:
        # pos = 'pos is NoneType'
        pos = 0
    # if servo_id is None:
    #     servo_id = 'servoid is NoneType'
    target = joint_id["joint_1"][1]
    # print(str(pos) + ', ' + str(target) + ', ' + str(servo_id) + ', ' + str(temp))
    servoWriteCmd(joint_id["joint_1"][0], command["MOVE_WRITE"],target-pos)



