import json
import unicodedata
from pathlib import Path

import pandas as pd

DATA = Path(__file__).resolve().parent / "data"
TR_DIR = DATA / "tr"
OUT = DATA / "translations.json"

df = pd.read_csv(DATA / "places.csv", encoding="utf-8-sig", dtype=str).fillna("")


def norm(s):
    """ปรับอักขระให้เป็นรูปแบบเดียวกัน และตัดช่องว่างทุกชนิดออก ใช้เทียบชื่อเท่านั้น"""
    return "".join(unicodedata.normalize("NFC", str(s)).split())


rows = {norm(r["name"]): r for _, r in df.iterrows()}

result = {}


def put(thai, lang, text):
    thai = str(thai).strip()
    if thai and text:
        result.setdefault(thai, {})[lang] = text


for lang in ("en", "zh"):
    entries = {}
    for f in sorted(TR_DIR.glob(f"{lang}_*.py")):
        ns = {}
        exec(f.read_text(encoding="utf-8"), ns)
        entries.update(ns.get("PLACES", {}))

    done = set()
    for name, (name_tr, parts_tr, reviews_tr) in entries.items():
        row = rows.get(norm(name))
        if row is None:
            print(f"[{lang}] ไม่พบใน CSV: {name}")
            continue
        done.add(norm(name))

        parts = row["description"].split()
        reviews = [x.strip() for x in row["reviews"].split("|") if x.strip()]

        put(row["name"], lang, name_tr)
        sep = "，" if lang == "zh" else ", "
        put(row["description"], lang, sep.join(parts_tr))

        if len(parts) == len(parts_tr):
            for a, b in zip(parts, parts_tr):
                put(a, lang, b)
        else:
            print(f"[{lang}] {name}: คำอธิบายมี {len(parts)} ส่วน แต่แปลมา {len(parts_tr)}")

        if len(reviews) == len(reviews_tr):
            for a, b in zip(reviews, reviews_tr):
                put(a, lang, b)
        else:
            print(f"[{lang}] {name}: รีวิวมี {len(reviews)} ข้อ แต่แปลมา {len(reviews_tr)}")

    missing = [r["name"] for k, r in rows.items() if k not in done]
    print(f"[{lang}] แปลแล้ว {len(done)} แห่ง ยังขาด {len(missing)} แห่ง")
    for n in missing[:10]:
        print("     ขาด:", n)

OUT.write_text(json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8")
print("บันทึกแล้ว", OUT)