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
lastFrame = None
firstFrame = None

fps = vs.get(cv2.CAP_PROP_FPS)

timestamps = [vs.get(cv2.CAP_PROP_POS_MSEC)]
calc_timestamps = [0.0]


fourcc = cv2.VideoWriter_fourcc(*'DIVX')
out = cv2.VideoWriter('output.avi', fourcc, 20.0, (int(vs.get(3)), int(vs.get(4))))

window_segs = 2
window_frames = window_segs * fps * 2
window = WindowList(round(window_frames))

window_offset = 0

while True:
    # grab the current frame and initialize the occupied/unoccupied
    # text
    ret, frame = vs.read()
    timestamps.append(vs.get(cv2.CAP_PROP_POS_MSEC))
    calc_timestamps.append(calc_timestamps[-1] + 1000 / fps)
    currentFrame = frame
    savedFrame = frame

    text = "Unoccupied"
    # if the frame could not be grabbed, then we have reached the end
    # of the video
    if currentFrame is None:
        break

    y_s = 0
    y_e = 280
    x_s = 280
    x_e = 460
    currentFrame = currentFrame[y_s:y_e, x_s:x_e]

    # resize the frame, convert it to grayscale, and blur it
    currentFrame = imutils.resize(currentFrame, width=500)
    gray = cv2.cvtColor(currentFrame, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (21, 21), 0)
    # if the first frame is None, initialize it
    if lastFrame is None:
        firstFrame = gray
        lastFrame = gray
        continue

    frameDelta = cv2.absdiff(lastFrame, firstFrame)
    thresh = cv2.threshold(frameDelta, 10, 255, cv2.THRESH_BINARY)[1]
    cnts = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL,
                            cv2.CHAIN_APPROX_SIMPLE)
    cnts = imutils.grab_contours(cnts)
    # loop over the contours
    for c in cnts:
        (x, y, w, h) = cv2.boundingRect(c)
        # if the contour is too small, ignore it or not
        # correspond to a normal human body, ignore it
        if cv2.contourArea(c) < 1000 or h / w < 3 or h < 400:
            continue
        # compute the bounding box for the contour, draw it on the frame,
        # and update the text
        cv2.rectangle(thresh, (x, y), (x + w, y + h), (255, 255, 0), 2)
        text = "Occupied"
        window_offset = window_frames

    cv2.rectangle(savedFrame, (x_s, y_s), (x_e, y_e), (0, 255, 0), 2)
    __draw_label(savedFrame, str(datetime.timedelta(milliseconds=calc_timestamps[-1])), (40,40), (255,255,0))

    window.append(savedFrame)
    if window_offset > 0:
        window_offset -= 1
        for image in window.list():
            out.write(image)
        window.clear()
    # show the frame and record if the user presses a key
    # cv2.imshow("Security Feed", currentFrame)
    # cv2.imshow("Thresh", thresh)
    key = cv2.waitKey(1) & 0xFF

    lastFrame = gray
    # if the `q` key is pressed, break from the lop
    if key == ord("q"):
        break
# cleanup the camera and close any open windows
out.release()

vs.stop() if args.get("video", None) is None else vs.release()

cv2.destroyAllWindows()
# _fourcc = cv2.VideoWriter_fourcc(*'MP4V')
# fourcc = cv2.VideoWriter_fourcc('m', 'p', '4', 'v')
# out = cv2.VideoWriter(video_name, fourcc, 20.0, (1080,960))
# for i in range(len(image_array)):
#     out.write(image_array[i])
