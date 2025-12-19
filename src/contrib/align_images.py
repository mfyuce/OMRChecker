import cv2
import numpy as np
import os
import glob
import math

# ---------------------------------------
# Blue marker detector (stronger version)
# ---------------------------------------

def find_blue_squares(img):
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

    # Wide blue threshold (more tolerant)
    lower_blue = np.array([80, 20, 20])
    upper_blue = np.array([150, 255, 255])

    mask = cv2.inRange(hsv, lower_blue, upper_blue)

    # Morphology to fix broken markers
    kernel = np.ones((7,7), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    mask = cv2.medianBlur(mask, 5)

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    squares = []
    for c in contours:
        area = cv2.contourArea(c)
        if area < 1500 or area > 80000:
            continue

        peri = cv2.arcLength(c, True)
        approx = cv2.approxPolyDP(c, 0.04 * peri, True)

        if len(approx) == 4 and cv2.isContourConvex(approx):
            squares.append(approx)

    return squares


# ---------------------------------------
# Order points safely
# ---------------------------------------

def order_points(pts):
    pts = np.array(pts).reshape(4, 2)
    rect = np.zeros((4, 2), dtype="float32")

    s = pts.sum(axis=1)
    rect[0] = pts[np.argmin(s)]      # top-left
    rect[3] = pts[np.argmax(s)]      # bottom-right

    diff = np.diff(pts, axis=1)
    rect[1] = pts[np.argmin(diff)]   # top-right
    rect[2] = pts[np.argmax(diff)]   # bottom-left

    return rect


# ---------------------------------------
# Fallback: rotate image by angle of edges
# ---------------------------------------

def auto_deskew(img):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray = cv2.bitwise_not(gray)

    thresh = cv2.threshold(gray, 0, 255,
                           cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]

    coords = np.column_stack(np.where(thresh > 0))
    angle = cv2.minAreaRect(coords)[-1]

    if angle < -45:
        angle = -(90 + angle)
    else:
        angle = -angle

    # rotate
    (h, w) = img.shape[:2]
    M = cv2.getRotationMatrix2D((w // 2, h // 2), angle, 1.0)
    rotated = cv2.warpAffine(img, M, (w, h),
                             flags=cv2.INTER_CUBIC,
                             borderMode=cv2.BORDER_REPLICATE)

    return rotated


# ---------------------------------------
# Align with markers or fallback
# ---------------------------------------

def align_page(img):
    squares = find_blue_squares(img)

    # ---------- CASE 1: Perfect 4 marker alignment ----------
    if len(squares) == 4:
        pts = []
        for sq in squares:
            M = cv2.moments(sq)
            cx = M["m10"] / M["m00"]
            cy = M["m01"] / M["m00"]
            pts.append([cx, cy])

        src = order_points(pts)

        W, H = 1700, 2200
        dst = np.float32([
            [100, 100],
            [W - 100, 100],
            [100, H - 100],
            [W - 100, H - 100],
        ])

        M = cv2.getPerspectiveTransform(src, dst)
        aligned = cv2.warpPerspective(img, M, (W, H))
        return aligned

    # ---------- CASE 2: Missing markers → deskew fallback ----------
    print("FALLBACK: deskew used (missing markers)")
    return auto_deskew(img)


# ---------------------------------------
# Process folder
# ---------------------------------------

def process_folder(in_folder="./pages", out_folder="./aligned"):
    os.makedirs(out_folder, exist_ok=True)

    files = glob.glob(os.path.join(in_folder, "*.png"))
    print(f"Found {len(files)} PNG files")

    for idx, f in enumerate(files, 1):
        try:
            img = cv2.imread(f)
            aligned = align_page(img)

            out_path = os.path.join(out_folder, os.path.basename(f))
            cv2.imwrite(out_path, aligned)

            print(f"[{idx}/{len(files)}] OK -> {out_path}")

        except Exception as e:
            print(f"[{idx}/{len(files)}] FAILED: {f} ({e})")


# --------------------------
# RUN
# --------------------------

if __name__ == "__main__":
    input_folder = "/home/fatihyuce/work/projects/tmp/optical_form/apps/OMRChecker/inputs/bu/MobileCamera/"
    output_folder = "/home/fatihyuce/work/projects/tmp/optical_form/apps/OMRChecker/inputs/bu/aligned/"
    process_folder(input_folder, output_folder)
