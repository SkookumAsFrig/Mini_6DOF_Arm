#!/usr/bin/python3

import serial
import time
import numpy as np
import matplotlib.pyplot as plt


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
    servoWriteCmd(0xFE, command["ID_READ"]) #send read command
 
    time.sleep(0.0055)  #delay

    count = serialHandle.inWaiting() #get number of bytes in serial buffer
    servid = None
    if count != 0: #if not empty
        recv_data = serialHandle.read(count) #read data
        # print('count is ' + str(count))
        if count == 7: #if it matches expected data length
            # print(recv_data)
            if recv_data[0] == 0x55 and recv_data[1] == 0x55 and recv_data[4] == 0x0E :
                #first and second bytes are 0x55, fifth byte is 0x0E (14), which is read id command
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
"joint_1" : [1, 100]
}

servoWriteCmd(joint_id["joint_1"][0], command["LOAD_UNLOAD_WRITE"],0)

init_time = time.time()
duration = 30
now_time = 0
report_dur = 3
old_rem_time = 0
kp = 30
ki = 0.2
err_int = 0
data = []
last_err = 0
tar_inc = 300


while now_time < duration:
    pos = readPosition(joint_id["joint_1"][0])
    # temp = readTemperature(joint_id["joint_1"][0])
    # if temp is None:
    #     temp = 'temp is NoneType'
    if pos is None:
        # pos = 'pos is NoneType'
        pos = 0

    target = joint_id["joint_1"][1]
    # print(str(pos) + ', ' + str(target) + ', ' + str(servo_id) + ', ' + str(temp))

    # Control law
    err = target-pos
    err_int += err
    if np.sign(err) != np.sign(last_err):
        err_int = 0

    # need round to keep motor input a integer
    motor_input = round(kp*err + ki*err_int)
    last_err = err

    # Limit motor input to real hardware range
    motor_input = max(min(motor_input, 1000), -1000)

    servoWriteCmd(joint_id["joint_1"][0], command["SERVO_MODE_WRITE"], 1, motor_input)

    now_time = time.time()-init_time
    rem_time = now_time%report_dur

    if old_rem_time>rem_time:
        print('control period: ' + str(rem_time + report_dur - old_rem_time))
        print(str(now_time)[0:6] + ' seconds have passed')
        servo_id = readID(1)
        if servo_id is None:
            servo_id = 'NoneType'
        print('servoID is ' + str(servo_id))

        # Advance target
        target += tar_inc
        
        # Limit position target to real hardware range
        joint_id["joint_1"][1] = max(min(target, 1000), 0)

    old_rem_time = rem_time
    data += [[now_time, pos]]

servoWriteCmd(joint_id["joint_1"][0], command["SERVO_MODE_WRITE"], 0)
servoWriteCmd(joint_id["joint_1"][0], command["LOAD_UNLOAD_WRITE"],0)

data = np.array(data)
fig = plt.plot(data[:,0], data[:,1])
plt.xlabel("Time (s)")
plt.ylabel("Position (sensor units)")
plt.title("Single Servo Motor Mode PID Response")
plt.show()
