import cv2
import numpy as np
import glob
import os


# ------------------------------------------------------
# 1. Blue square detection (robust to brightness & noise)
# ------------------------------------------------------

def find_blue_squares(img):
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

    # wide tolerance to catch all blue tones
    lower = np.array([70, 20, 20])
    upper = np.array([150, 255, 255])
    mask = cv2.inRange(hsv, lower, upper)

    # clean mask
    mask = cv2.medianBlur(mask, 5)

    cnts, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    squares = []
    for c in cnts:
        x, y, w, h = cv2.boundingRect(c)

        # size filter → blue boxes are roughly 60–120 px each
        if 40 < w < 200 and 40 < h < 200:
            squares.append((x, y, w, h))

    # sort by area (largest 2 should be top-left and top-right)
    squares = sorted(squares, key=lambda b: b[2] * b[3], reverse=True)

    return squares[:2]  # return only top 2 blue squares


# ------------------------------------------------------
# 2. Detect left and right vertical lines using Hough
# ------------------------------------------------------

def detect_vertical_lines(img):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # edges
    edges = cv2.Canny(gray, 50, 150, apertureSize=3)

    # Hough lines
    lines = cv2.HoughLinesP(
        edges,
        rho=1,
        theta=np.pi / 180,
        threshold=120,
        minLineLength=400,
        maxLineGap=20
    )

    if lines is None:
        raise Exception("No lines found")

    left_x = None
    right_x = None

    for ln in lines:
        x1, y1, x2, y2 = ln[0]

        # vertical line check (difference between x1 and x2 small)
        if abs(x1 - x2) < 10:
            if left_x is None or x1 < left_x:
                left_x = x1
            if right_x is None or x1 > right_x:
                right_x = x1

    return left_x, right_x


# ------------------------------------------------------
# 3. Compute crop area based on markers + lines
# ------------------------------------------------------

def compute_crop_area(img, squares, left_x, right_x):
    # squares contain two entries: (x,y,w,h)
    # find upper y coordinate (top of form)
    top_y = min(s[1] for s in squares) - 30
    if top_y < 0:
        top_y = 0

    # full height
    h = img.shape[0]

    # horizontal crop based on vertical lines
    left = max(left_x - 20, 0)
    right = min(right_x + 20, img.shape[1])

    bottom = h - 20

    return left, top_y, right, bottom


# ------------------------------------------------------
# 4. Combined function to crop aligned area
# ------------------------------------------------------

def align_crop(img):
    # 1) find 2 blue squares (top-left + top-right)
    squares = find_blue_squares(img)

    if len(squares) < 2:
        raise Exception("Could not find both blue squares")

    # 2) detect left/right vertical boundaries
    left_x, right_x = detect_vertical_lines(img)

    if left_x is None or right_x is None:
        raise Exception("Vertical lines not detected")

    # 3) compute cropping region
    left, top, right, bottom = compute_crop_area(img, squares, left_x, right_x)

    # 4) crop
    crop = img[top:bottom, left:right]

    return crop


# ------------------------------------------------------
# 5. Batch processing
# ------------------------------------------------------

def process_folder(in_folder="./pages", out_folder="./aligned"):
    os.makedirs(out_folder, exist_ok=True)

    files = glob.glob(os.path.join(in_folder, "*.png"))
    print(f"Found {len(files)} PNG files")

    for idx, f in enumerate(files, 1):
        try:
            img = cv2.imread(f)
            out = align_crop(img)

            out_path = os.path.join(out_folder, os.path.basename(f))
            cv2.imwrite(out_path, out)

            print(f"[{idx}] OK → {out_path}")

        except Exception as e:
            print(f"[{idx}] FAIL {f} → {e}")


if __name__ == "__main__":
    input_folder = "/home/fatihyuce/work/projects/tmp/optical_form/apps/OMRChecker/inputs/bu/MobileCamera/"
    output_folder = "/home/fatihyuce/work/projects/tmp/optical_form/apps/OMRChecker/inputs/bu/aligned/"
    process_folder(input_folder, output_folder)
