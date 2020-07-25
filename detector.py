import argparse

import cv2
import imutils
import datetime
from WindowList import WindowList

def __draw_label(img, text, pos, bg_color):
    font_face = cv2.FONT_HERSHEY_SIMPLEX
    scale = 0.4
    color = (0, 0, 0)
    thickness = cv2.FILLED
    margin = 2

    txt_size = cv2.getTextSize(text, font_face, scale, thickness)

    end_x = pos[0] + txt_size[0][0] + margin
    end_y = pos[1] - txt_size[0][1] - margin

    cv2.rectangle(img, pos, (end_x, end_y), bg_color, thickness)
    cv2.putText(img, text, pos, font_face, scale, color, 1, cv2.LINE_AA)

# construct the argument parser and parse the arguments
ap = argparse.ArgumentParser()
ap.add_argument("-v", "--video", help="path to the video file")
args = vars(ap.parse_args())


vs = cv2.VideoCapture(args["video"])
# initialize the first frame in the video stream
firstFrame = None

fps = vs.get(cv2.CAP_PROP_FPS)

timestamps = [vs.get(cv2.CAP_PROP_POS_MSEC)]
calc_timestamps = [0.0]


fourcc = cv2.VideoWriter_fourcc(*'DIVX')
out = cv2.VideoWriter('output.avi', fourcc, 20.0, (int(vs.get(3)), int(vs.get(4))))

times_file = open("times.txt", "+w")

window_segs = 5
window_frames = round(window_segs * fps)
window = WindowList(window_frames)

window_offset = 0

y_s = 0
y_e = 400
x_s = 200
x_e = 800

min_height = 150

while True:
    # grab the current frame and initialize the occupied/unoccupied
    _, frame = vs.read()
    timestamps.append(vs.get(cv2.CAP_PROP_POS_MSEC))
    calc_timestamps.append(calc_timestamps[-1] + 1000 / fps)

    text = "Unoccupied"
    # if the frame could not be grabbed, then we have reached the end
    # of the video
    if frame is None:
        break
    movement_rectangle = frame[y_s:y_e, x_s:x_e]

    # resize the frame, convert it to grayscale, and blur it
    movement_rectangle = imutils.resize(movement_rectangle, width=500)
    gray = cv2.cvtColor(movement_rectangle, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (21, 21), 0)
    # if the first frame is None, initialize it
    if firstFrame is None:
        firstFrame = gray
        continue

    frameDelta = cv2.absdiff(gray, firstFrame)
    thresh = cv2.threshold(frameDelta, 10, 255, cv2.THRESH_BINARY)[1]
    cnts = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL,
                            cv2.CHAIN_APPROX_SIMPLE)
    cnts = imutils.grab_contours(cnts)
    # loop over the contours

    str_time = str(datetime.timedelta(milliseconds=calc_timestamps[-1]))
    cv2.rectangle(frame, (x_s, y_s), (x_e, y_e), (0, 255, 0), 2)
    __draw_label(frame, str_time, (40,40), (255,255,0))

    for c in cnts:
        (x, y, w, h) = cv2.boundingRect(c)
        # if the contour is too small, ignore it or not
        # correspond to a normal human body, ignore it

        if cv2.contourArea(c) < 500 or h / w < 3 or h < min_height:
            continue
        # compute the bounding box for the contour, draw it on the frame,
        # and update the text

        if window_offset == 0:
            times_file.write(f'{str_time}\n')
            print(str_time)

        window_offset = window_frames

    window.append(frame)
    if window_offset > 0:
        window_offset -= 1
        for image in window.list():
            out.write(image)
        window.clear()

    # cv2.imshow("Thresh", thresh)
    key = cv2.waitKey(1) & 0xFF

    # if the `q` key is pressed, break from the lop
    if key == ord("q"):
        break
# cleanup the camera and close any open windows
out.release()

vs.stop() if args.get("video", None) is None else vs.release()

times_file.close()
cv2.destroyAllWindows()
