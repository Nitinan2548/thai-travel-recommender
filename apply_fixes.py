import shutil
from pathlib import Path

import pandas as pd

from recommender import DATA_DIR

csv_path = DATA_DIR / "places.csv"
shutil.copy(csv_path, DATA_DIR / "places_before_fix.csv")  # สำรองไฟล์เดิมไว้ก่อน

df = pd.read_csv(csv_path, encoding="utf-8-sig", dtype=str, keep_default_na=False)
photos = Path(__file__).resolve().parent / "photos"
names = df["name"].str.strip()

# 1) 8 แห่งที่เคยติด 429 (ลำดับต้องตรงกับ fetch_failed.py)
NAMES8 = ["มัสยิดกรือเซะ", "อ่าวพังงา", "ทะเลน้อย", "พระธาตุเชิงชุม",
          "ดอยอ่างขาง", "หาดชะอำ", "ภูทับเบิก", "เขาค้อ"]
for i, idx in enumerate(df[names.isin(NAMES8)].index, start=1):
    found = sorted(photos.glob(f"place_{i:02d}.*"))
    if found:
        df.at[idx, "image_url"] = f"photos/{found[0].name}"
        print("แก้แล้ว:", df.at[idx, "name"], "->", df.at[idx, "image_url"])
    else:
        print("ยังไม่มีรูป:", df.at[idx, "name"], f"(ต้องมี photos/place_{i:02d}.*)")

# 2) เชียงคาน และ แพะเมืองผี (เดิม 404)
FIX = {
    "เชียงคาน": ("chiangkhan.jpg",
                 "https://commons.wikimedia.org/wiki/File:Mekong_in_Chiang_Khan_4.jpg"),
    "แพะเมืองผี": ("phae.jpg",
                   "https://commons.wikimedia.org/wiki/File:Phae_Mueang_Phi_Forest_Park1.jpg"),
}
for name, (fname, page) in FIX.items():
    for idx in df.index[names == name]:
        if (photos / fname).exists():
            df.at[idx, "image_url"] = f"photos/{fname}"
            df.at[idx, "image_source"] = page
            df.at[idx, "image_credit"] = "Wikimedia Commons (ดูผู้ถ่ายและสัญญาอนุญาตที่หน้าไฟล์ต้นทาง)"
            print("แก้แล้ว:", name, "->", df.at[idx, "image_url"])
        else:
            print("ยังไม่มีรูป:", name, f"(ต้องมี photos/{fname})")

df.to_csv(csv_path, index=False, encoding="utf-8-sig")
print("\nบันทึก places.csv แล้ว (ไฟล์เดิมสำรองไว้ที่ places_before_fix.csv)")