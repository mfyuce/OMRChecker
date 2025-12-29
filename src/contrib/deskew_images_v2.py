import os
import glob
import cv2
import numpy as np

# İstersen sabit boyut kullan:
# TARGET_W, TARGET_H = 1371, 3287   # yüksek çözünürlük
TARGET_W, TARGET_H = None, None     # None -> orijinal boyut korunur


def find_markers(bgr):
    """
    4 köşe karesini HSV renge göre bulur.
    Senin formlardaki turkuaz karelere göre aralık ayarlı.
    """
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)

    # turkuaz renk aralığı (gerekirse değiştir)
    lower = np.array([80, 40, 80], dtype=np.uint8)
    upper = np.array([110, 255, 255], dtype=np.uint8)

    mask = cv2.inRange(hsv, lower, upper)

    contours, _ = cv2.findContours(
        mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
    )

    markers = []
    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area < 500:   # küçük gürültüleri at
            continue
        x, y, w, h = cv2.boundingRect(cnt)
        markers.append((x, y, w, h))

    return markers


def warp_with_markers(bgr, target_w=None, target_h=None):
    """
    4 kareyi kullanarak perspektif düzeltir.
    Karelerin merkezlerini hedef görüntünün dört köşesine map eder.
    """
    h0, w0 = bgr.shape[:2]
    if target_w is None:
        target_w = w0
    if target_h is None:
        target_h = h0

    markers = find_markers(bgr)
    if len(markers) != 4:
        raise RuntimeError(f"4 köşe karesi bulunamadı, {len(markers)} adet bulundu.")

    # y'ye göre, sonra x'e göre sırala
    markers_sorted = sorted(markers, key=lambda r: (r[1], r[0]))
    top = sorted(markers_sorted[:2], key=lambda r: r[0])      # soldan sağa
    bottom = sorted(markers_sorted[2:], key=lambda r: r[0])   # soldan sağa
    tl, tr = top
    bl, br = bottom

    def center(rect):
        x, y, w, h = rect
        return [x + w / 2.0, y + h / 2.0]

    src = np.float32([
        center(tl),  # top-left
        center(tr),  # top-right
        center(bl),  # bottom-left
        center(br),  # bottom-right
    ])

    dst = np.float32([
        [0, 0],
        [target_w, 0],
        [0, target_h],
        [target_w, target_h],
    ])

    M = cv2.getPerspectiveTransform(src, dst)
    warped = cv2.warpPerspective(bgr, M, (target_w, target_h))

    return warped


def process_folder(input_dir, output_dir):
    os.makedirs(output_dir, exist_ok=True)

    paths = sorted(glob.glob(os.path.join(input_dir, "*.png")))
    print(f"{len(paths)} dosya bulundu.")

    for i, path in enumerate(paths, 1):
        print(f"[{i}/{len(paths)}] {path}")
        img = cv2.imread(path, cv2.IMREAD_COLOR)
        if img is None:
            print("  -> okunamadı, geçiliyor.")
            continue

        try:
            aligned = warp_with_markers(img, TARGET_W, TARGET_H)
        except Exception as e:
            print(f"  -> hizalama hatası: {e}")
            continue

        out_path = os.path.join(output_dir, os.path.basename(path))
        cv2.imwrite(out_path, aligned)
        print(f"  -> {out_path} kaydedildi.")


if __name__ == "__main__":
    # Örnek kullanım:
    # input klasör:  raw_scans/
    # output klasör: aligned/


    input_folder = "/home/fatihyuce/work/projects/tmp/optical_form/apps/OMRChecker/back/makeup"
    output_folder = "/home/fatihyuce/work/projects/tmp/optical_form/apps/OMRChecker/back/makeup_deskewed"
    process_folder(input_folder, output_folder)
