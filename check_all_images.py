import time
from pathlib import Path

import requests

from recommender import load_data

ROOT = Path(__file__).resolve().parent
HEADERS = {"User-Agent": "thai-travel-recommender/1.0 (personal project)"}


def check_url(url):
    """คืนรหัส HTTP ถ้าเจอ 429 จะรอแล้วลองใหม่สูงสุด 4 ครั้ง"""
    for attempt in range(4):
        resp = requests.get(url, headers=HEADERS, timeout=15, stream=True)
        resp.close()
        if resp.status_code == 429:
            time.sleep(5 * (attempt + 1))
            continue
        return resp.status_code
    return 429


df = load_data()
bad = []

for _, r in df.iterrows():
    src = str(r.get("image_url", "")).strip()
    reason = None
    if not src:
        reason = "ไม่มี image_url"
    elif src.startswith("http"):
        try:
            status = check_url(src)
            if status != 200:
                reason = f"HTTP {status}"
        except Exception as e:
            reason = f"เชื่อมต่อไม่ได้ ({type(e).__name__})"
        time.sleep(1)  # หน่วงระหว่างแต่ละรูป ไม่ให้ยิงถี่เกินไป
    else:
        p = Path(src)
        if not p.is_absolute():
            p = ROOT / src
        if not p.exists():
            reason = "ไม่พบไฟล์ในเครื่อง"
    if reason:
        bad.append((r["province"], r["name"], reason))

print(f"ตรวจ {len(df)} แห่ง รูปมีปัญหา {len(bad)} แห่ง\n")
by_prov = {}
for prov, name, reason in bad:
    by_prov.setdefault(prov, []).append(f"{name} [{reason}]")
for prov in sorted(by_prov):
    print(f"■ {prov}")
    for item in by_prov[prov]:
        print("    -", item)