import os
import csv
import base64
from io import BytesIO
from PIL import Image
import pytesseract

# If needed on Windows:
# pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

INPUT_DIR = "/home/fatihyuce/work/projects/tmp/optical_form/apps/OMRChecker/inputs/bu_makeup/makeup"
#OUTPUT_DIR = "/home/fatihyuce/work/projects/tmp/optical_form/apps/OMRChecker/results/2/mb2_deskewed"

OMR_CSV = "/home/fatihyuce/work/projects/tmp/optical_form/apps/OMRChecker/results/makeup/makeup/Results/Results_08PM.csv"
FULL_HTML  = "full_report.html"
LIGHT_HTML = "light_report.html"

# (left, top, right, bottom) – senin formuna göre:
NAME_REGION = (460, 0, 1800, 75)
ID_REGION   = (460, 90, 1800, 160)

DO_OCR = False  # hafif formda metin görmek istersen True yap


def ocr_digits_from_crop(img: Image.Image) -> str:
    gray = img.convert("L")
    text = pytesseract.image_to_string(
        gray,
        lang="eng",
        config="--psm 7 -c tessedit_char_whitelist=0123456789"
    )
    return "".join(ch for ch in text if ch.isdigit())


def ocr_name_from_crop(img: Image.Image) -> str:
    gray = img.convert("L")
    text = pytesseract.image_to_string(
        gray,
        # lang="eng+tur",
        lang="eng",
        config="--psm 7 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyzĞÜŞİÖÇğıüşiöç .-"
    )
    return text.strip()


def image_to_base64(img: Image.Image) -> str:
    buf = BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode("ascii")


def load_omr_csv(path):
    rows = {}
    with open(path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            fname = r.get("filename") or r.get("file") or list(r.values())[0]
            rows[fname] = r
    return rows


def get_score(omr_row: dict) -> str:
    # CSV’deki muhtemel score kolon isimleri
    for key in ("score", "Score", "SCORE", "total", "Total", "TOTAL", "points", "Points"):
        if key in omr_row and omr_row[key] != "":
            return omr_row[key]
    return "-"


def main():
    omr_data = load_omr_csv(OMR_CSV)
    full_rows = []
    light_rows = []

    for fname in sorted(os.listdir(INPUT_DIR)):
        if not fname.lower().endswith((".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp")):
            continue

        full_in_path = os.path.join(INPUT_DIR, fname)
        img = Image.open(full_in_path)

        # --- NAME crop ---
        name_crop = img.crop(NAME_REGION)
        name_b64 = image_to_base64(name_crop)
        ocr_name = ocr_name_from_crop(name_crop) if DO_OCR else ""

        # --- ID crop ---
        id_crop = img.crop(ID_REGION)
        id_b64 = image_to_base64(id_crop)
        ocr_id = ocr_digits_from_crop(id_crop) if DO_OCR else ""

        # --- OMR data ---
        omr = omr_data.get(fname, {})
        omr_html = ",".join(
            [f"<b>{k}</b>: {v}" for k, v in omr.items() if k not in ("filename", "file", "")]
        )
        score = get_score(omr)

        # ==== FULL REPORT SATIRI ====
        full_row = f"""
        <tr> 
            <td><b>{fname.replace(".png","")}</b></td>

            <td> 
                <img src="data:image/png;base64,{name_b64}" style="max-height:80px;width:300px" />
                {'<br><b>OCR:</b> ' + ocr_name if DO_OCR else ''}
            </td>

            <td> 
                <img src="data:image/png;base64,{id_b64}" style="max-height:80px;width:300px" />
                {'<br><b>OCR:</b> ' + ocr_id if DO_OCR else ''}
            </td>

            <td>{omr_html}</td> 
        </tr>
        """
        full_rows.append(full_row)

        # ==== LIGHT REPORT SATIRI ====
        # Hafif form: sadece Name, ID, Score
        # Eğer DO_OCR=False ise metin yok, sadece görsel + skor olur.
        light_row = f"""
        <tr>
            <td><b>{fname.replace(".png","")}</b></td>

            <td>
                <img src="data:image/png;base64,{name_b64}" style="max-height:40px;width:220px" />
                {'<small>' + ocr_name + '</small>' if DO_OCR and ocr_name else ''}
            </td>

            <td>
                <img src="data:image/png;base64,{id_b64}" style="max-height:40px;width:220px" />
                {'<small>' + ocr_id + '</small>' if DO_OCR and ocr_id else ''}
            </td>

            <td style="text-align:center;"><b>{score}</b></td>
        </tr>
        """
        light_rows.append(light_row)

    # ===== FULL REPORT HTML =====
    full_html = f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>Full OMR Report</title>
<style>
    body {{ font-family: Arial, sans-serif; }}
    table {{ border-collapse: collapse; width: 100%; }}
    th, td {{ border: 1px solid #ccc; padding: 8px; vertical-align: top; }}
    th {{ background: #eee; }}
</style>
</head>
<body>

<h1>Full OMR Report</h1>
<p>Tüm optik formlar bir arada: Name &amp; ID alanı görüntüsü, OMR ve puanlar.</p>

<table>
<thead>
<tr> 
    <th>File Name</th>
    <th>Name</th>
    <th>ID</th>
    <th>OMR Data (Answers / Score)</th> 
</tr>
</thead>
<tbody>
{''.join(full_rows)}
</tbody>
</table>

</body>
</html>
"""
    with open(FULL_HTML, "w", encoding="utf-8") as f:
        f.write(full_html)

    # ===== LIGHT REPORT HTML =====
    light_html = f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>OMR Light Report</title>
<style>
    body {{ font-family: Arial, sans-serif; }}
    table {{ border-collapse: collapse; width: 60%; margin:auto; }}
    th, td {{ border: 1px solid #ccc; padding: 6px; vertical-align: middle; }}
    th {{ background: #f7f7f7; }}
    td {{ text-align: left; }}
</style>
</head>
<body>

<h2 style="text-align:center;">OMR Light Report (Name / ID / Score)</h2>

<table>
<thead>
<tr>
    <th>File Name</th>
    <th>Name</th>
    <th>ID</th>
    <th>Score</th>
</tr>
</thead>
<tbody>
{''.join(light_rows)}
</tbody>
</table>

</body>
</html>
"""
    with open(LIGHT_HTML, "w", encoding="utf-8") as f:
        f.write(light_html)

    print(f"\nDone!\n  Full report : {FULL_HTML}\n  Light report: {LIGHT_HTML}\n")


if __name__ == "__main__":
    main()
