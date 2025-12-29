import cv2
import numpy as np

def deskew_image(path_in, path_out=None, max_angle=3):
    img = cv2.imread(path_in)
    if img is None:
        raise ValueError(f"Cannot read image: {path_in}")
    if "27" in path_in:
        pass
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # optional: crop header region only
    H, W = gray.shape
    gray = gray[0:int(H*0.3), :]   # top 30%

    gray_inv = cv2.bitwise_not(gray)
    _, thresh = cv2.threshold(
        gray_inv, 0, 255,
        cv2.THRESH_BINARY | cv2.THRESH_OTSU
    )

    coords = np.column_stack(np.where(thresh > 0))
    if coords.size == 0:
        if path_out is not None:
            cv2.imwrite(path_out, img)
        return img, 0.0

    rect = cv2.minAreaRect(coords)
    raw_angle = rect[-1]

    # OpenCV 0–180° convention
    if raw_angle > 90:
        angle = raw_angle - 180
    else:
        angle = raw_angle

    print(f"raw_angle={raw_angle:.2f}, normalized_angle={angle:.2f}")

    # Only apply small corrections
    if abs(angle) <= max_angle:
        (h, w) = img.shape[:2]
        center = (w // 2, h // 2)
        M = cv2.getRotationMatrix2D(center, angle, 1.0)
        rotated = cv2.warpAffine(
            img, M, (w, h),
            flags=cv2.INTER_CUBIC,
            borderMode=cv2.BORDER_REPLICATE
        )
        if path_out is not None:
            cv2.imwrite(path_out, rotated)
        return rotated, angle
    else:
        # Skew looks unrealistic → do nothing
        if path_out is not None:
            cv2.imwrite(path_out, img)
        return img, 0.0


import cv2
import numpy as np
import math

def estimate_skew_hough(path):
    img = cv2.imread(path)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # hafif blur + kenar
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    edges = cv2.Canny(blur, 50, 150, apertureSize=3)

    # yatay çizgileri bul
    lines = cv2.HoughLinesP(edges, 1, np.pi/180,
                            threshold=150,
                            minLineLength=200,
                            maxLineGap=20)

    if lines is None:
        return 0.0

    angles = []
    for x1, y1, x2, y2 in lines[:, 0]:
        dx, dy = x2 - x1, y2 - y1
        if abs(dx) < 50:          # dikey çizgileri at
            continue
        angle = math.degrees(math.atan2(dy, dx))
        angles.append(angle)

    if not angles:
        return 0.0

    return float(np.mean(angles))   # örn. ~0.94°

def deskew_with_hough(path_in, path_out, max_angle=5):
    img = cv2.imread(path_in)
    angle = estimate_skew_hough(path_in)
    print(f"Estimated skew: {angle:.2f}°")

    if abs(angle) > max_angle:
        # çok garipse hiç dokunma
        cv2.imwrite(path_out, img)
        return img, 0.0

    (h, w) = img.shape[:2]
    center = (w // 2, h // 2)
    # sayfayı düzlemek için -angle döndür
    M = cv2.getRotationMatrix2D(center, -angle, 1.0)
    rotated = cv2.warpAffine(
        img, M, (w, h),
        flags=cv2.INTER_CUBIC,
        borderMode=cv2.BORDER_REPLICATE
    )
    cv2.imwrite(path_out, rotated)
    return rotated, angle


def fix_perspective(img,path_out=None):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    edges = cv2.Canny(blur, 50, 150)

    # Find contours
    cnts, _ = cv2.findContours(edges, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    cnts = sorted(cnts, key=cv2.contourArea, reverse=True)

    page_contour = None
    for c in cnts:
        peri = cv2.arcLength(c, True)
        approx = cv2.approxPolyDP(c, 0.02 * peri, True)
        if len(approx) == 4:
            page_contour = approx
            break

    if page_contour is None:
        print("No 4-corner page contour found.")
        return img

    # Order points (tl, tr, br, bl) and compute warp
    pts = page_contour.reshape(4, 2).astype("float32")

    # Order by sum and diff (simple heuristic)
    s = pts.sum(axis=1)
    diff = np.diff(pts, axis=1)

    tl = pts[np.argmin(s)]
    br = pts[np.argmax(s)]
    tr = pts[np.argmin(diff)]
    bl = pts[np.argmax(diff)]

    src = np.array([tl, tr, br, bl], dtype="float32")

    # Choose output size; e.g., keep same width/height
    width = int(max(
        np.linalg.norm(br - bl),
        np.linalg.norm(tr - tl)
    ))
    height = int(max(
        np.linalg.norm(tr - br),
        np.linalg.norm(tl - bl)
    ))

    dst = np.array([
        [0, 0],
        [width - 1, 0],
        [width - 1, height - 1],
        [0, height - 1]
    ], dtype="float32")

    M = cv2.getPerspectiveTransform(src, dst)
    warped = cv2.warpPerspective(img, M, (width, height))

    if path_out is not None:
        cv2.imwrite(path_out, warped)

    return warped

# img = cv2.imread("/home/fatihyuce/work/projects/tmp/optical_form/apps/OMRChecker/back/mb2/paper_0.png")
# img = fix_perspective(img,
#                   "/home/fatihyuce/work/projects/tmp/optical_form/apps/OMRChecker/back/mb2/paper_0_pers.png")
# rotated, angle = deskew_image("/home/fatihyuce/work/projects/tmp/optical_form/apps/OMRChecker/back/mb2/paper_0.png",
#                               "/home/fatihyuce/work/projects/tmp/optical_form/apps/OMRChecker/back/mb2/paper_0_deskewed.png")
# rotated, angle = deskew_image("/home/fatihyuce/work/projects/tmp/optical_form/apps/OMRChecker/back/mb2/paper_0_pers.png",
#                               "/home/fatihyuce/work/projects/tmp/optical_form/apps/OMRChecker/back/mb2/paper_0_pers_deskewed.png")

#img, angle = deskew_image("scan.png")  # or call deskew on warped image directly