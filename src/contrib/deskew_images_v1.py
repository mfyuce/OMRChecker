import glob
import os
from image_works import deskew_with_hough
from natsort import natsorted
# ------------------------------------------------------
# 5. Batch işlem
# ------------------------------------------------------

def process_folder(in_folder="./pages", out_folder="./aligned"):
    os.makedirs(out_folder, exist_ok=True)

    files = natsorted(glob.glob(os.path.join(in_folder, "*.png")))
    print(f"Found {len(files)} PNG files")

    for idx, f in enumerate(files, 1):
        try:
            out_path = os.path.join(out_folder, os.path.basename(f))

            rotated, angle = deskew_with_hough(f,
                                          out_path)

            print(f"[{idx}] OK → {out_path}")

        except Exception as e:
            print(f"[{idx}] FAIL {f} → {e}")


# ------------------------------------------------------
# 6. Çalıştır
# ------------------------------------------------------

if __name__ == "__main__":
    input_folder = "/home/fatihyuce/work/projects/tmp/optical_form/apps/OMRChecker/back/makeup"
    output_folder = "/home/fatihyuce/work/projects/tmp/optical_form/apps/OMRChecker/back/makeup_deskewed"
    process_folder(input_folder, output_folder)
