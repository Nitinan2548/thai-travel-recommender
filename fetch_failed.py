import re
import time
from pathlib import Path
from urllib.parse import quote, unquote

import requests

from recommender import load_data

ROOT = Path(__file__).resolve().parent
# แก้ your-email@example.com เป็นอีเมลจริงของคุณ
HEADERS = {"User-Agent": "thai-travel-recommender/1.0 (your-email@example.com)"}
NAMES = ["มัสยิดกรือเซะ", "อ่าวพังงา", "ทะเลน้อย", "พระธาตุเชิงชุม",
         "ดอยอ่างขาง", "หาดชะอำ", "ภูทับเบิก", "เขาค้อ"]


def fetch(filename, dest):
    base = "https://commons.wikimedia.org/wiki/Special:FilePath/" + quote(filename)
    for suffix in ("?width=960", "?width=640", ""):
        for attempt in range(4):
            r = requests.get(base + suffix, headers=HEADERS, timeout=90)
            print(f"    ลอง {suffix or 'ต้นฉบับ'} ครั้งที่ {attempt + 1}: HTTP {r.status_code}")
            if r.status_code == 200 and r.headers.get("Content-Type", "").startswith("image"):
                dest.write_bytes(r.content)
                return True
            if r.status_code == 429:
                ra = r.headers.get("Retry-After", "")
                time.sleep(min(int(ra), 60) if ra.isdigit() else 10 * (attempt + 1))
                continue
            break  # 404 หรืออื่น ๆ ลองขนาดถัดไป
    return False


out = ROOT / "photos"
out.mkdir(exist_ok=True)
df = load_data()

for i, (_, r) in enumerate(df[df["name"].isin(NAMES)].iterrows(), start=1):
    if list(out.glob(f"place_{i:02d}.*")):
        print(f"{r['name']}  ->  มีไฟล์ place_{i:02d} แล้ว ข้าม")
        continue
    url = str(r["image_url"])
    m = re.search(r"/commons/(?:thumb/)?[0-9a-f]/[0-9a-f]{2}/([^/]+)", url)
    if not m:
        print("อ่านชื่อไฟล์จากลิงก์ไม่ได้:", r["name"], url)
        continue
    filename = unquote(m.group(1))
    ext = Path(filename).suffix.lower()
    if ext not in (".jpg", ".jpeg", ".png", ".webp", ".gif"):
        ext = ".jpg"
    save_as = f"place_{i:02d}{ext}"
    print(f"{r['name']}  ({filename})")
    if fetch(filename, out / save_as):
        print(f"  -> image_url ใหม่: photos/{save_as}")
    else:
        print("  -> โหลดไม่สำเร็จ")
    time.sleep(3)