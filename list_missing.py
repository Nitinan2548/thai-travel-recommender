import json
import unicodedata
from pathlib import Path

import pandas as pd

DATA = Path(__file__).resolve().parent / "data"
df = pd.read_csv(DATA / "places.csv", encoding="utf-8-sig", dtype=str).fillna("")
tr = json.loads((DATA / "translations.json").read_text(encoding="utf-8"))


def norm(s):
    return "".join(unicodedata.normalize("NFC", str(s)).split())


tr_norm = {norm(k): v for k, v in tr.items()}

for lang in ("en", "zh"):
    missing = [n for n in df["name"] if not tr_norm.get(norm(n), {}).get(lang)]
    print(f"[{lang}] ขาด {len(missing)} แห่ง")
    for n in missing[:15]:
        print("   ", n)