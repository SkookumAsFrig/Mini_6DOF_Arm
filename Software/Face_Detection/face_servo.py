# USAGE
# python build_face_dataset.py --cascade haarcascade_frontalface_default.xml --output dataset/adrian

# import the necessary packages
from imutils.video import VideoStream
import argparse
import imutils
import time
import cv2
import os
import numpy
import random

import serial
import csv
import RPi.GPIO as GPIO
from threading import Thread

GPIO.setmode(GPIO.BCM)
GPIO.setup(5, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

# define global variable
global joint_id
global command
global off_mode
global light_on_sw
global show_now
show_now = False
light_on_sw = False
off_mode = True

# initialize servo id and postion
joint_id = {  #[real servo id, home position]
    "joint_1": [5, 852],
    "joint_2": [1, 597],
    "joint_3": [2, 135],
    "joint_4": [4, 510],
    "joint_5": [6, 900],
    "joint_6": [3, 474]
}


def show_routine(routine_file):
    # show robot dance routine
    # para:
    #   routine_file: a recorded CSV file
    global joint_id
    global show_now
    global light_on_sw
    global command

    if not light_on_sw:
        show_now = True
        init_time = time.time()
        duration = 0

        with open(routine_file) as csvfile:
            pamreader = csv.reader(csvfile, delimiter=',')
            for row in pamreader:
                duration = time.time() - init_time
                try:
                    newrow = list(map(float, row))
                except Exception:
                    continue
                rec_time = newrow[-1]
                while (duration < rec_time):
                    duration = time.time() - init_time
                    time.sleep(0.0000001)

                ind = 0
                for key in joint_id.keys():
                    servoWriteCmd(joint_id[key][0],
                                  command["SERVO_MODE_WRITE"], 0)
                    servoWriteCmd(joint_id[key][0], command["MOVE_WRITE"],
                                  int(newrow[ind]), 0)
                    ind += 1

        for key in joint_id.keys():
            servoWriteCmd(joint_id[key][0], command["SERVO_MODE_WRITE"], 0)
            servoWriteCmd(joint_id[key][0], command["MOVE_WRITE"],
                          joint_id[key][1], 0)

        show_now = False


def GPIO5cb():
    # listen GPIO 5 and show light-switch routine
    # as long as the switch is off
    # two modes (fast mode and slow mode) for this routine
    global light_on_sw
    global joint_id
    global command
    global off_mode
    while True:
        time.sleep(1)
        if light_on_sw and not show_now:

            if off_mode:
                off_file = 'light_off.csv'
            else:
                off_file = 'light_off2.csv'

            off_mode = not off_mode

            for key in joint_id.keys():
                servoWriteCmd(joint_id[key][0], command["SERVO_MODE_WRITE"], 0)
                servoWriteCmd(joint_id[key][0], command["MOVE_WRITE"],
                              joint_id[key][1], 0)

            time.sleep(1.5)

            init_time = time.time()
            duration = 0

            with open(off_file) as csvfile:
                pamreader = csv.reader(csvfile, delimiter=',')
                for row in pamreader:
                    duration = time.time() - init_time
                    try:
                        newrow = list(map(float, row))
                    except Exception:
                        continue
                    rec_time = newrow[-1]
                    while (duration < rec_time):
                        duration = time.time() - init_time
                        time.sleep(0.0000001)

                    ind = 0
                    for key in joint_id.keys():
                        servoWriteCmd(joint_id[key][0],
                                      command["SERVO_MODE_WRITE"], 0)
                        servoWriteCmd(joint_id[key][0], command["MOVE_WRITE"],
                                      int(newrow[ind]), 0)
                        ind += 1

            togg = True
            tog_speed = 1000
            times = 0

            while tog_speed >= 150:
                time.sleep(0.03)
                if togg:
                    servoWriteCmd(joint_id["joint_6"][0],
                                  command["SERVO_MODE_WRITE"], 1, tog_speed)
                else:
                    servoWriteCmd(joint_id["joint_6"][0],
                                  command["SERVO_MODE_WRITE"], 1, -tog_speed)
                togg = not togg
                if times < 2:
                    times += 1
                else:
                    tog_speed -= 150
                    times = 0

            light_on_sw = False

            servoWriteCmd(joint_id["joint_6"][0], command["SERVO_MODE_WRITE"],
                          0)
            servoWriteCmd(joint_id['joint_3'][0], command["MOVE_WRITE"], 250,
                          0)


# initialize and start the light-switch deamon
light_off_thread = Thread(target=GPIO5cb, daemon=True)
light_off_thread.daemon = True
light_off_thread.start()

# initialize serial and servo command
serialHandle = serial.Serial("/dev/ttyUSB0", 115200)  #115200 baud rate

command = {
    "MOVE_WRITE": 1,
    "POS_READ": 28,
    "SERVO_MODE_WRITE": 29,
    "LOAD_UNLOAD_WRITE": 31,
    "SERVO_MOVE_STOP": 12,
    "TEMP_READ": 26
}


#No need to split into higher and lower bytes, this function does it already. Parameter # is # of different params.
def servoWriteCmd(id, cmd, par1=None, par2=None):
    # write commands to servos
    # para:
    #   id: servo id
    #   cmd: real command
    buf = bytearray(b'\x55\x55')
    try:
        len = 3  #length is 3 if no commands
        buf1 = bytearray(b'')

        ## verify data
        if par1 is not None:
            len += 2  #add 2 to data length
            buf1.extend([
                (0xff & par1), (0xff & (par1 >> 8))
            ])  #split into lower and higher bytes, store in buffer
        if par2 is not None:
            len += 2
            buf1.extend([
                (0xff & par2), (0xff & (par2 >> 8))
            ])  #split into lower and higher bytes, store in buffer
        buf.extend([(0xff & id), (0xff & len), (0xff & cmd)])
        buf.extend(buf1)

        ## checksum
        sum = 0x00
        for b in buf:  #sum
            sum += b
        sum = sum - 0x55 - 0x55  #remove two beginning 0x55
        sum = ~sum  #take not
        buf.append(0xff & sum)  #add lower byte into buffer
        serialHandle.write(buf)  #send
    except Exception as e:
        print(e)


def readPosition(id):
    # read the position of each servo
    # para:
    #   id: servo id
    serialHandle.flushInput()
    servoWriteCmd(id, command["POS_READ"])  #send read command

    time.sleep(0.0055)  #delay

    count = serialHandle.inWaiting()  #get number of bytes in serial buffer
    pos = None
    if count != 0:  #if not empty
        recv_data = serialHandle.read(count)  #read data
        if count == 8:  #if it matches expected data length
            if recv_data[0] == 0x55 and recv_data[1] == 0x55 and recv_data[
                    4] == 0x1C:
                #first and second bytes are 0x55, fifth byte is 0x1C (28), which is read position command
                pos = 0xffff & (recv_data[5] | (0xff00 & (recv_data[6] << 8))
                                )  #combine data for valid read

    return pos


def readTemperature(id):
    # read the temperature of each servo
    # para:
    #   id: servo id
    serialHandle.flushInput()
    servoWriteCmd(id, command["TEMP_READ"])  #send read command

    time.sleep(0.01)  #delay

    count = serialHandle.inWaiting()  #get number of bytes in serial buffer
    tem = None
    if count != 0:  #if not empty
        recv_data = serialHandle.read(count)  #read data
        if count == 7:  #if it matches expected data length
            if recv_data[0] == 0x55 and recv_data[1] == 0x55 and recv_data[
                    4] == 0x1A:
                #first and second bytes are 0x55, fifth byte is 0x1A (26), which is read temperature command
                tem = recv_data[5]

    return tem


# construct the argument parser and parse the arguments
ap = argparse.ArgumentParser()
ap.add_argument("-c",
                "--cascade",
                required=True,
                help="path to where the face cascade resides")
args = vars(ap.parse_args())

# load OpenCV's Haar cascade for face detection from disk
detector = cv2.CascadeClassifier(args["cascade"])

# initialize the video stream, allow the camera sensor to warm up
# the size of captured frames is set to width=320, height=240
# frame per second is 32
print("[INFO] starting video stream...")
# vs = VideoStream(src=0).start()
vs = VideoStream(usePiCamera=True, resolution=(320, 240), framerate=32).start()
time.sleep(2.0)
total = 0

#servo control variables
cont_var = 0
last_input = True
dist_center_x = 0
hinc = 1
linc = 1

show_time = time.time()
d_lim = 30
t_duration = 0
t_init = time.time()

# loop over the frames from the video stream
while True:
    # grab the frame from the threaded video stream and resize the frame
    # resize the frame size with fixed width/height ratio => width=400, height=300
    frame = vs.read()
    frame = imutils.resize(frame, width=400)

    # detect faces in the grayscale frame
    rects = detector.detectMultiScale(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY),
                                      scaleFactor=1.1,
                                      minNeighbors=5,
                                      minSize=(60, 60))

    # camera center coordinates
    camera_center_x = 200
    camera_center_y = 150

    # loop over the face detections and control the servos
    # if the camera does detects some faces, then further
    # control the robot. Otherwise, it does not move
    if len(rects) > 0:
        # refine the bounding boxes by using only the maximum area bbx
        arr = numpy.zeros((len(rects), 1))

        for idx, (x, y, w, h) in enumerate(rects, start=1):
            arr[idx - 1] = w * h

        max_ind = numpy.argmax(arr)

        x, y, w, h = rects[max_ind]

        # draw the bounding box on the original frame
        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
        # the bounding box center coordinates
        bbx_center_x = x + w / 2
        bbx_center_y = y + h / 2
        # center distance
        dist_center_x = camera_center_x - bbx_center_x
        dist_center_y = camera_center_y - bbx_center_y
        print('---------------------------------------------------')
        print(
            'Index: {} Camear center: {} Face center: {} Distance: {}'.format(
                idx, (camera_center_x, camera_center_y),
                (bbx_center_x, bbx_center_y), (dist_center_x, dist_center_y)))

        # read the position of joint 1 and 3
        pos = readPosition(joint_id['joint_1'][0])
        pos2 = readPosition(joint_id['joint_3'][0])

        if pos:
            print('joint 1 position: {}'.format(pos))
            # limit the movement angle for joint 1
            if ((pos < 300) and (dist_center_x < 0)):
                servoWriteCmd(joint_id['joint_1'][0],
                              command["SERVO_MODE_WRITE"], 1,
                              abs(int(2 * dist_center_x)))
            elif ((pos > 900) and (dist_center_x > 0)):
                servoWriteCmd(joint_id['joint_1'][0],
                              command["SERVO_MODE_WRITE"], 1,
                              -abs(int(2 * dist_center_x)))
            else:
                servoWriteCmd(joint_id['joint_1'][0],
                              command["SERVO_MODE_WRITE"], 1,
                              int(3 * dist_center_x))

        if pos2:
            print('joint 3 position: {}'.format(pos2))
            # limit the movement angle for joint 3
            if pos2 > 150 :
                if dist_center_y < 0:
                    if linc < 100:
                        linc += 1
                    hinc = 1
                    servoWriteCmd(joint_id['joint_3'][0],
                                  command["SERVO_MODE_WRITE"], 0)
                    servoWriteCmd(joint_id['joint_3'][0],
                                  command["MOVE_WRITE"], pos2 - linc, 0)

            if pos2 < 900:
                if dist_center_y > 0:
                    linc = 1
                    if hinc < 500:
                        hinc += 1
                    servoWriteCmd(joint_id['joint_3'][0],
                                  command["SERVO_MODE_WRITE"], 0)
                    servoWriteCmd(joint_id['joint_3'][0],
                                  command["MOVE_WRITE"], pos2 + hinc, 0)
                    print(pos2 + hinc)
    else:
        servoWriteCmd(joint_id['joint_1'][0], command["SERVO_MODE_WRITE"], 1,
                      0)

    # show dance routine randomly
    duration = time.time() - show_time
    if duration > d_lim:
        print('show')
        duration = 0
        show_time = time.time()
        d_lim = random.randint(90, 180)
        f_ind = random.randint(1, 7)
        show_routine('rand_rout' + str(f_ind) + '.csv')

    # show the output frame
    cv2.imshow("Frame", frame)
    key = cv2.waitKey(1) & 0xFF

    t_duration = time.time() - t_init

    if t_duration > 5:
        t_init = time.time()
        tem_out = []
        for key in joint_id.keys():
            tem_out.append(readTemperature(joint_id[key][0]))

        print(tem_out)

    now_input = GPIO.input(5)
    if not now_input and not last_input:
        cont_var += 1
    else:
        cont_var = 0

    if cont_var > 6:
        cont_var = -10
        light_on_sw = True

    last_input = now_input

# do a bit of cleanup
print("[INFO] {} face images stored".format(total))
print("[INFO] cleaning up...")
cv2.destroyAllWindows()
vs.stop()
