"""ตรวจรูปที่ใส่เองใน data/images ว่าแอปจะหาเจอหรือไม่

วิธีใช้ (ในโฟลเดอร์โปรเจกต์ ข้าง app.py):
    python check_images.py
"""
import difflib
from pathlib import Path

import pandas as pd

BASE = Path(__file__).resolve().parent
IMAGE_DIR = BASE / "data" / "images"
EXTS = (".jpg", ".jpeg", ".png", ".webp")


def main():
    names = (pd.read_csv(BASE / "data" / "places.csv", encoding="utf-8-sig")
             ["name"].astype(str).str.strip().tolist())
    known = set(names)

    images_py = BASE / "images.py"
    if not images_py.exists() or "IMAGE_DIR" not in images_py.read_text(
            encoding="utf-8"):
        print("!! images.py ยังเป็นเวอร์ชันเก่า ไม่รองรับรูปใน data/images")
        print("   ให้ทับ images.py (และ app.py) ด้วยไฟล์ล่าสุด แล้วรีสตาร์ท Streamlit\n")

    if not IMAGE_DIR.exists():
        print("ยังไม่มีโฟลเดอร์ data/images")
        return
    files = sorted(p for p in IMAGE_DIR.iterdir() if p.is_file())
    if not files:
        print("โฟลเดอร์ data/images ว่างเปล่า (ยังไม่ได้ย้ายไฟล์เข้ามา)")
        return

    ok = 0
    for f in files:
        stem, ext = f.stem, f.suffix.lower()
        if ext in EXTS and stem in known:
            print(f"[ใช้ได้]  {f.name}")
            ok += 1
            continue

        if ext not in EXTS:
            why = f"นามสกุล '{f.suffix}' ไม่รองรับ (ใช้ .jpg .jpeg .png .webp)"
            if not f.suffix:
                why = ("ไม่มีนามสกุลไฟล์ (เปิดแสดงนามสกุลใน File Explorer "
                       "แล้วตั้งชื่อเป็น ชื่อสถานที่.jpg)")
        elif Path(stem).suffix.lower() in EXTS:
            why = (f"นามสกุลซ้อนกัน ({Path(stem).suffix}{f.suffix}) "
                   f"ให้เปลี่ยนเป็น '{Path(stem).stem}{f.suffix}'")
        elif stem.strip() in known:
            why = "มีช่องว่างหน้า/หลังชื่อไฟล์ ให้ลบช่องว่างออก"
        else:
            close = difflib.get_close_matches(stem, names, n=1, cutoff=0.6)
            if close:
                why = (f"ไม่ตรงกับสถานที่ใด ใกล้เคียง '{close[0]}' "
                       f"ให้เปลี่ยนชื่อเป็น '{close[0]}{f.suffix}'")
            else:
                why = ("ไม่ตรงกับชื่อสถานที่ใดใน places.csv "
                       "ให้ตั้งชื่อใหม่ให้ตรงกับคอลัมน์ name")
        print(f"[ใช้ไม่ได้] {f.name}  ->  {why}")

    print(f"\nสรุป: ใช้ได้ {ok} / {len(files)} ไฟล์")


if __name__ == "__main__":
    main()
