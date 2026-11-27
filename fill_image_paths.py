import shutil
import unicodedata
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent
CSV = ROOT / "data" / "places.csv"
IMG = ROOT / "data" / "images"
EXTS = {".jpg", ".jpeg", ".png", ".webp"}


def norm(s):
    return "".join(unicodedata.normalize("NFC", str(s)).split())


files = {norm(p.stem): p for p in IMG.iterdir() if p.suffix.lower() in EXTS}

shutil.copy(CSV, ROOT / "data" / "places_backup_images.csv")
df = pd.read_csv(CSV, encoding="utf-8-sig", dtype=str).fillna("")
if "image_url" not in df.columns:
    df["image_url"] = ""

filled, still = 0, []
for i, r in df.iterrows():
    if r["image_url"].strip():
        continue
    p = files.get(norm(r["name"]))
    if p:
        df.at[i, "image_url"] = f"data/images/{p.name}"
        filled += 1
    else:
        still.append(f'{r["province"]} - {r["name"]}')

df.to_csv(CSV, index=False, encoding="utf-8-sig")
print(f"เติมให้แล้ว {filled} แห่ง ยังไม่มีรูป {len(still)} แห่ง")
for s in still:
    print("   ", s)