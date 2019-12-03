# USAGE
# python build_face_dataset.py --cascade haarcascade_frontalface_default.xml --output dataset/adrian

# import the necessary packages
from imutils.video import VideoStream
import argparse
import imutils
import time
import cv2
import os

# construct the argument parser and parse the arguments
ap = argparse.ArgumentParser()
ap.add_argument("-c",
                "--cascade",
                required=True,
                help="path to where the face cascade resides")
ap.add_argument("-o",
                "--output",
                required=True,
                help="path to output directory")
args = vars(ap.parse_args())

# load OpenCV's Haar cascade for face detection from disk
detector = cv2.CascadeClassifier(args["cascade"])

# initialize the video stream, allow the camera sensor to warm up,
# and initialize the total number of example faces written to disk
# thus far
# the size of captured frames is set to width=320, height=240
# frame per second is 32
print("[INFO] starting video stream...")
# vs = VideoStream(src=0).start()
vs = VideoStream(usePiCamera=True, resolution=(320, 240), framerate=32).start()
time.sleep(2.0)
total = 0

# loop over the frames from the video stream
while True:
    # grab the frame from the threaded video stream, clone it, (just
    # in case we want to write it to disk), and then resize the frame
    # so we can apply face detection faster
    # resize the frame size with fixed width/height ratio => width=400, height=300
    frame = vs.read()
    orig = frame.copy()
    frame = imutils.resize(frame, width=400)

    # detect faces in the grayscale frame
    rects = detector.detectMultiScale(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY),
                                      scaleFactor=1.1,
                                      minNeighbors=5,
                                      minSize=(30, 30))

    camera_center_x = 200
    camera_center_y = 150

    # loop over the face detections and draw them on the frame
    for idx, (x, y, w, h) in enumerate(rects, start=1):
        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
        bbx_center_x = (x + w) / 2
        bbx_center_y = (y + h) / 2
        dist_center_x = abs(camera_center_x - bbx_center_x)
        dist_center_y = abs(camera_center_y - bbx_center_y)
        print('---------------------------------------------------')
        print(
            'Index: {} Camear center: {} Face center: {} Distance: {}'.format(
                idx, (camera_center_x, camera_center_y),
                (bbx_center_x, bbx_center_y), (dist_center_x, dist_center_y)))

    # show the output frame
    cv2.imshow("Frame", frame)
    key = cv2.waitKey(1) & 0xFF

    # if the `k` key was pressed, write the *original* frame to disk
    # so we can later process it and use it for face recognition
    if key == ord("k"):
        p = os.path.sep.join(
            [args["output"], "{}.png".format(str(total).zfill(5))])
        cv2.imwrite(p, orig)
        total += 1

    # if the `q` key was pressed, break from the loop
    elif key == ord("q"):
        break

# do a bit of cleanup
print("[INFO] {} face images stored".format(total))
print("[INFO] cleaning up...")
cv2.destroyAllWindows()
vs.stop()
