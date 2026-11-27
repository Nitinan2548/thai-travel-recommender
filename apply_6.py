import shutil
from pathlib import Path

import pandas as pd

from recommender import DATA_DIR

ROOT = Path(__file__).resolve().parent
csv_path = DATA_DIR / "places.csv"
shutil.copy(csv_path, DATA_DIR / "places_before_apply6.csv")  # สำรองไว้ก่อน

CREDIT_NEW = "Wikimedia Commons (ดูผู้ถ่ายและสัญญาอนุญาตที่หน้าไฟล์ต้นทาง)"

# ชื่อสถานที่ -> (ไฟล์ในเครื่อง, ชื่อไฟล์บน Commons ถ้าเปลี่ยนไปใช้รูปใหม่ ไม่งั้นใส่ None)
FIX = {
    "อ่าวพังงา":      ("place_01.jpg", "Phang Nga - Thailand (12192457234).jpg"),
    "ภูทับเบิก":      ("place_02.jpg", None),
    "เขาค้อ":         ("place_03.jpg", "Khao Kho banner.jpg"),
    "พระธาตุเชิงชุม":  ("place_04.jpg", None),
    "มัสยิดกรือเซะ":   ("place_05.jpg", None),
    "หาดชะอำ":        ("place_06.jpg", None),
}

df = pd.read_csv(csv_path, encoding="utf-8-sig", dtype=str, keep_default_na=False)
names = df["name"].str.strip()

for name, (fname, commons_file) in FIX.items():
    idxs = df.index[names == name]
    if len(idxs) == 0:
        print("ไม่พบแถว:", name)
        continue
    if not (ROOT / "photos" / fname).exists():
        print("ยังไม่มีรูป:", name, f"(ต้องมี photos/{fname})")
        continue
    for idx in idxs:
        df.at[idx, "image_url"] = f"photos/{fname}"
        if commons_file:  # เปลี่ยนไปใช้รูปใหม่ ต้องอัปเดตเครดิตและต้นทางด้วย
            page = "https://commons.wikimedia.org/wiki/File:" + commons_file.replace(" ", "_")
            df.at[idx, "image_source"] = page
            df.at[idx, "image_credit"] = CREDIT_NEW
        print("แก้แล้ว:", name, "->", df.at[idx, "image_url"])

df.to_csv(csv_path, index=False, encoding="utf-8-sig")
print("\nบันทึก places.csv แล้ว (ไฟล์เดิมสำรองไว้ที่ places_before_apply6.csv)")