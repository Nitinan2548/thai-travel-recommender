import sys
import time
from pathlib import Path
from urllib.parse import quote

import requests

HEADERS = {"User-Agent": "thai-travel-recommender/1.0 (personal project)"}


def download_commons(filename, save_as, width=1280):
    """ดาวน์โหลดรูปจาก Wikimedia Commons ไปไว้ที่ photos/"""
    url = ("https://commons.wikimedia.org/wiki/Special:FilePath/"
           + quote(filename.replace(" ", "_")) + f"?width={width}")
    out = Path(__file__).resolve().parent / "photos"
    out.mkdir(exist_ok=True)

    for attempt in range(5):
        r = requests.get(url, headers=HEADERS, timeout=30)
        if r.status_code == 429:          # ขอถี่เกิน -> รอแล้วลองใหม่
            time.sleep(5 * (attempt + 1))
            continue
        r.raise_for_status()
        (out / save_as).write_bytes(r.content)
        print("บันทึกแล้ว:", out / save_as)
        return
    print("ไม่สำเร็จ ลองใหม่ภายหลัง")


if __name__ == "__main__":
    # ใช้: python download_image.py "ชื่อไฟล์บน Commons" ชื่อที่จะบันทึก.jpg
    download_commons(sys.argv[1], sys.argv[2])