import pdb
import time
import cv2
import imutils
import torch
from facenet_pytorch import MTCNN
from imutils.video import VideoStream
from PIL import Image
from threading import Thread


def detect(vs, mtcnn, device, show):
    while True:
        # grab the frame from the threaded video stream, clone it, (just
        # in case we want to write it to disk), and then resize the frame
        # so we can apply face detection faster
        # resize the frame size with fixed width/height ratio => width=400, height=300
        frame_raw = vs.read()
        # frame_raw = imutils.resize(frame_raw, width=400)

        # convert to PIL image format
        frame_converted = cv2.cvtColor(frame_raw, cv2.COLOR_BGR2RGB)
        frame = Image.fromarray(frame_converted)
        camera_center_x = frame.size[0] / 2
        camera_center_y = frame.size[1] / 2

        boxes, _ = mtcnn.detect(frame)

        # loop over the face detections and draw them on the frame
        if boxes is not None:
            for idx, box in enumerate(boxes, start=1):
                x_left, y_left, x_right, y_right = int(box[0]), int(
                    box[1]), int(box[2]), int(box[3])
                cv2.rectangle(frame_raw, (x_left, y_left), (x_right, y_right),
                              (0, 255, 0), 2)
                bbx_center_x = (x_right - x_left) / 2
                bbx_center_y = (y_right - y_left) / 2
                dist_center_x = abs(camera_center_x - bbx_center_x)
                dist_center_y = abs(camera_center_y - bbx_center_y)
                print('---------------------------------------------------')
                print(
                    'Index: {} Camera center: {}  Face center: {} Distance: {}'
                    .format(idx, (camera_center_x, camera_center_y),
                            (bbx_center_x, bbx_center_y),
                            (dist_center_x, dist_center_y)))
                # print('sleep')
                # time.sleep(5)
                # print('start')

        if show:
            # show the output frame
            cv2.imshow("Frame", frame_raw)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    # When everything done, release the capture
    cv2.destroyAllWindows()


if __name__ == '__main__':

    # initialize the video stream, allow the camera sensor to warm up,
    # and initialize the total number of example faces written to disk
    # thus far
    # the size of captured frames is set to width=320, height=240
    # frame per second is 32
    print("[INFO] starting video stream...")
    # vs = VideoStream(src=0).start()
    vs = VideoStream(usePiCamera=True, resolution=(160, 128),
                     framerate=32).start()
    time.sleep(2.0)

    device = torch.device('cuda:0' if torch.cuda.is_available() else 'cpu')
    print('Running on device: {}'.format(device))

    mtcnn = MTCNN(image_size=80,
                  margin=0,
                  min_face_size=20,
                  thresholds=[0.6, 0.7, 0.7],
                  factor=0.709,
                  prewhiten=True,
# keep_all=True,
                  device=device)

    detect(vs, mtcnn, device, show=True)

    # # running with Thread
    # detect_thread = Thread(target=detect, args=(vs, mtcnn, device, False, ), daemon=True)
    # detect_thread.start()
