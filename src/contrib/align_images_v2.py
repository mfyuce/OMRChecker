import cv2
import numpy as np
import glob
import os

# ------------------------------------------------------
# 0. Küçük açı deskew (sadece hafif sağ/sol eğimi düzelt)
# ------------------------------------------------------

def deskew_small_angle(img, max_angle=6):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray_inv = cv2.bitwise_not(gray)

    # sayfa içeriğini binarize et
    thresh = cv2.threshold(
        gray_inv, 0, 255,
        cv2.THRESH_BINARY | cv2.THRESH_OTSU
    )[1]

    coords = np.column_stack(np.where(thresh > 0))
    if coords.size == 0:
        return img  # güvenlik

    angle = cv2.minAreaRect(coords)[-1]

    # minAreaRect klasiği: -90..0 aralığı
    if angle < -45:
        angle = -(90 + angle)
    else:
        angle = -angle

    # sadece küçük açıları uygula, yoksa hiç döndürme
    if abs(angle) > max_angle:
        return img

    (h, w) = img.shape[:2]
    M = cv2.getRotationMatrix2D((w // 2, h // 2), angle, 1.0)
    rotated = cv2.warpAffine(
        img, M, (w, h),
        flags=cv2.INTER_CUBIC,
        borderMode=cv2.BORDER_REPLICATE
    )
    return rotated


# ------------------------------------------------------
# 1. Mavi kare tespiti
# ------------------------------------------------------

def find_blue_squares(img):
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

    lower = np.array([70, 20, 20])
    upper = np.array([150, 255, 255])
    mask = cv2.inRange(hsv, lower, upper)

    mask = cv2.medianBlur(mask, 5)

    cnts, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    squares = []
    for c in cnts:
        x, y, w, h = cv2.boundingRect(c)
        # mavi karelerin tipik boyutu
        if 40 < w < 200 and 40 < h < 200:
            squares.append((x, y, w, h))

    squares = sorted(squares, key=lambda b: b[2] * b[3], reverse=True)
    return squares[:2]   # üst sol + üst sağ


# ------------------------------------------------------
# 2. Sol/sağ dikey çizgi tespiti (HoughLinesP)
# ------------------------------------------------------

def detect_vertical_lines(img):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 50, 150, apertureSize=3)

    lines = cv2.HoughLinesP(
        edges,
        rho=1,
        theta=np.pi/180,
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
        if abs(x1 - x2) < 10:  # dikey çizgi
            if left_x is None or x1 < left_x:
                left_x = x1
            if right_x is None or x1 > right_x:
                right_x = x1

    return left_x, right_x


# ------------------------------------------------------
# 3. Crop alanını hesapla
# ------------------------------------------------------

def compute_crop_area(img, squares, left_x, right_x):
    top_y = min(s[1] for s in squares) - 30
    if top_y < 0:
        top_y = 0

    h, w = img.shape[:2]

    left = max(left_x - 20, 0)
    right = min(right_x + 20, w)

    bottom = h - 20

    return left, top_y, right, bottom


# ------------------------------------------------------
# 4. Hepsi bir arada: önce deskew sonra crop
# ------------------------------------------------------

def align_crop(img):
    # 0) küçük açı deskew
    img = deskew_small_angle(img, max_angle=6)

    # 1) mavi kareler
    squares = find_blue_squares(img)
    if len(squares) < 2:
        raise Exception("Could not find both blue squares")

    # 2) sol/sağ dikey çizgiler
    left_x, right_x = detect_vertical_lines(img)
    if left_x is None or right_x is None:
        raise Exception("Vertical lines not detected")

    # 3) crop alanı
    left, top, right, bottom = compute_crop_area(img, squares, left_x, right_x)

    crop = img[top:bottom, left:right]
    return crop


# ------------------------------------------------------
# 5. Batch işlem
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


# ------------------------------------------------------
# 6. Çalıştır
# ------------------------------------------------------

if __name__ == "__main__":
    input_folder = "/home/fatihyuce/work/projects/tmp/optical_form/apps/OMRChecker/inputs/bu/MobileCamera/"
    output_folder = "/home/fatihyuce/work/projects/tmp/optical_form/apps/OMRChecker/inputs/bu/aligned1/"
    process_folder(input_folder, output_folder)
