"""ดึงรูปของสถานที่จริงจาก Wikipedia / Wikimedia Commons ใส่ลง data/places.csv

วิธีใช้ (รันในโฟลเดอร์โปรเจกต์ ข้างโฟลเดอร์ data):
    python fix_images.py                    # เติมเฉพาะแถวที่ยังไม่มีรูปที่เชื่อถือได้
    python fix_images.py --refresh          # ค้นหาใหม่ทุกแถว
    python fix_images.py --debug "วัดอรุณ"   # ทดสอบสถานที่เดียว พร้อมแสดงเหตุผล

ลำดับการค้นหา:
  1. เปิดบทความ Wikipedia ไทยด้วยชื่อตรง ๆ (ตามรีไดเรกต์ได้
     เช่น "วัดพระแก้ว" -> "วัดพระศรีรัตนศาสดาราม")
  2. ค้นหาใน Wikipedia ไทย (ชื่อบทความต้องมีชื่อสถานที่ครบ)
  3. ถ้าบทความไทยไม่มีรูป ใช้รูปจากบทความอังกฤษของสถานที่เดียวกัน
  4. ค้นไฟล์รูปบน Wikimedia Commons

การตรวจความถูกต้อง: ถ้าบทความมีพิกัด ต้องห่างจาก lat/lon ใน places.csv
ไม่เกิน 40 กม. และลิงก์รูปต้องเปิดได้จริง ถ้าไม่ผ่านจะเว้นว่างไว้

ไฟล์เดิมถูกสำรองเป็น data/places.csv.bak
รายชื่อที่ไม่มีรูปถูกบันทึกที่ data/missing_images.csv
"""
import argparse
import math
import re
import shutil
import sys
import time
from pathlib import Path
from urllib.parse import quote

import pandas as pd
import requests

DATA = Path(__file__).resolve().parent / "data" / "places.csv"
MAX_KM = 40
MAX_KM_EXACT = 100  # ชื่อบทความตรงกับชื่อสถานที่เป๊ะ ยอมให้พิกัดคลาดเคลื่อนได้มากกว่า
IMAGE_DIR = Path(__file__).resolve().parent / "data" / "images"
LOCAL_EXTS = (".jpg", ".jpeg", ".png", ".webp")
IMAGE_COLS = ["image_url", "image_credit", "image_source"]
SKIP = re.compile(
    r"(?i)(^|[^a-z])(map|locator|flag|logo|seal)([^a-z]|$)|\.svg")
PAGE_PROPS = dict(prop="pageimages|coordinates|langlinks|pageprops",
                  ppprop="disambiguation", piprop="thumbnail",
                  pithumbsize=960, lllang="en", lllimit=50, colimit=50)
DEBUG = False

session = requests.Session()
CONTACT = ""  # (ไม่บังคับ) ใส่อีเมลของคุณ เช่น "me@example.com" Wikimedia ขอให้ระบุผู้ติดต่อ
session.headers.update({"User-Agent": "thai-travel-recommender/1.0 (student project"
                        + (f"; {CONTACT}" if CONTACT else "") + ")"})


def dbg(*args):
    if DEBUG:
        print("   [debug]", *args)


NOTES = []


def note(message):
    """เก็บเหตุผลที่ไม่ได้รูป ไว้แสดงท้ายบรรทัด [ไม่มีรูป]"""
    NOTES.append(message)
    dbg(message)


def check_url(url):
    """คืน (ใช้ได้ไหม, รายละเอียด): ลิงก์ต้องตอบ 200 และเป็นไฟล์รูปจริง"""
    if not url or not url.startswith(("http://", "https://")):
        return False, "ลิงก์ไม่ถูกต้อง"
    detail = ""
    for attempt in range(2):
        try:
            r = session.get(url, stream=True, timeout=15)
            status = r.status_code
            ctype = r.headers.get("content-type", "")
            r.close()
        except requests.RequestException as error:
            return False, f"เชื่อมต่อไม่ได้ ({type(error).__name__})"
        if status == 200 and ctype.startswith("image/"):
            return True, "OK"
        detail = f"HTTP {status}" if status != 200 else f"ไม่ใช่รูป ({ctype})"
        if status == 429 and attempt == 0:
            time.sleep(3)
            continue
        break
    return False, detail


def url_ok(url):
    return check_url(url)[0]


def clean_name(name):
    """'เกาะหลีเป๊ะ (สตูล)' -> 'เกาะหลีเป๊ะ'"""
    return re.sub(r"\s*[\(\[].*?[\)\]]", "", name).strip()


def norm(text):
    return re.sub(r"\s+", "", text).lower()


def num(value):
    return None if pd.isna(value) else float(value)


def km(lat1, lon1, lat2, lon2):
    p = math.pi / 180
    a = (math.sin((lat2 - lat1) * p / 2) ** 2
         + math.cos(lat1 * p) * math.cos(lat2 * p)
         * math.sin((lon2 - lon1) * p / 2) ** 2)
    return 12742 * math.asin(math.sqrt(a))


LAST_CALL = [0.0]
MIN_INTERVAL = 0.7  # วินาที ระหว่างการเรียก API แต่ละครั้ง (กัน Wikimedia จำกัดความถี่)


def api(lang, **params):
    base = {"action": "query", "format": "json"}
    base.update(params)
    host = lang if "." in lang else f"{lang}.wikipedia.org"
    for attempt in range(4):
        wait = MIN_INTERVAL - (time.time() - LAST_CALL[0])
        if wait > 0:
            time.sleep(wait)
        LAST_CALL[0] = time.time()
        try:
            r = session.get(f"https://{host}/w/api.php", params=base,
                            timeout=20)
        except requests.RequestException as error:
            dbg(f"{host}: เชื่อมต่อไม่ได้ ({type(error).__name__}) ลองใหม่")
            time.sleep(2 * (attempt + 1))
            continue
        if r.status_code == 429 or r.status_code >= 500:
            try:
                delay = int(r.headers.get("Retry-After", ""))
            except ValueError:
                delay = 4 * 2 ** attempt
            dbg(f"{host}: HTTP {r.status_code} รอ {delay} วินาที")
            time.sleep(min(delay, 30))
            continue
        try:
            data = r.json()
        except ValueError:
            note(f"API {host}: HTTP {r.status_code} ตอบกลับไม่ใช่ JSON")
            return {}
        if "error" in data:
            code = data["error"].get("code", "?")
            dbg(f"{host}: error {code}")
            if code in ("ratelimited", "maxlag"):
                time.sleep(4 * (attempt + 1))
                continue
            note(f"API {host}: error {code}")
            return {}
        return data.get("query", {}).get("pages", {})
    note(f"API {host}: ถูกจำกัดความถี่/เชื่อมต่อไม่ได้ (ลองซ้ำ 4 ครั้งแล้ว)")
    return {}


def near(page, lat, lon, limit=MAX_KM):
    """บทความมีพิกัด -> ต้องไม่ไกลเกิน limit; ไม่มีพิกัด -> ไม่มีเหตุให้ปฏิเสธ"""
    coords = page.get("coordinates")
    if coords and lat is not None and lon is not None:
        c = coords[0]
        return km(lat, lon, c["lat"], c["lon"]) <= limit
    return True


def accept(name, lat, lon, page):
    """ผลค้นหา: บทความนี้คือสถานที่เดียวกับแถวนี้หรือไม่"""
    a, b = norm(name), norm(page.get("title", ""))
    if not a or not b:
        return False
    coords = page.get("coordinates")
    if coords and lat is not None and lon is not None:
        return near(page, lat, lon) and (a in b or b in a)
    # ไม่มีพิกัดให้ตรวจ: ชื่อบทความต้องมีชื่อสถานที่ครบ
    return a in b


def thumb_of(page):
    t = page.get("thumbnail", {}).get("source", "")
    return "" if (not t or SKIP.search(t)) else t


def wiki_link(lang, title):
    return f"https://{lang}.wikipedia.org/wiki/" + quote(title.replace(" ", "_"))


def page_result(page, lang, lat, lon):
    """เอารูปจากบทความที่ยอมรับแล้ว (ถ้าไม่มีรูป ลองบทความอังกฤษ)"""
    title = page["title"]
    thumb = thumb_of(page)
    dbg(f"{lang}: {title!r} รูป={'มี' if thumb else 'ไม่มี'} "
        f"พิกัด={page.get('coordinates')}")
    if not thumb:
        raw = page.get("thumbnail", {}).get("source", "")
        note(f"'{title}' รูปหลักถูกคัดทิ้ง (แผนที่/ธง/โลโก้/svg)" if raw
             else f"'{title}' ไม่มีรูปหลัก")
    if thumb:
        return thumb, f"Wikipedia: {title}", wiki_link(lang, title)
    for ll in page.get("langlinks", []):
        en_title = ll.get("*") or ll.get("title")
        if ll.get("lang") != "en" or not en_title:
            continue
        en_pages = api("en", titles=en_title, redirects=1,
                       prop="pageimages|coordinates", piprop="thumbnail",
                       pithumbsize=960, colimit=50)
        for p in en_pages.values():
            t = thumb_of(p)
            dbg(f"en: {p.get('title')!r} รูป={'มี' if t else 'ไม่มี'}")
            if t and near(p, lat, lon, MAX_KM_EXACT):
                return t, f"Wikipedia: {p['title']}", wiki_link("en", p["title"])
    return None


def wiki_image(name, lat, lon):
    # 1) เปิดด้วยชื่อตรง ๆ (ตามรีไดเรกต์)
    variants = [name, name.replace(" ", "")]
    for prefix in ("อุทยานแห่งชาติ", "อำเภอ"):
        if not name.startswith(prefix):
            variants.append(prefix + name)
    for n, title in enumerate(dict.fromkeys(variants)):
        report = note if n == 0 else dbg  # แจ้งเหตุผลเฉพาะชื่อจริง ไม่รวมชื่อที่เดา
        pages = api("th", titles=title, redirects=1, **PAGE_PROPS)
        for page in pages.values():
            if "missing" in page or "disambiguation" in page.get("pageprops", {}):
                report(f"ชื่อตรง '{title}': ไม่มีบทความ/เป็นหน้าแก้ความกำกวม")
                continue
            if not near(page, lat, lon, MAX_KM_EXACT):
                report(f"ชื่อตรง '{title}': พิกัดบทความไกลเกินไป")
                continue
            result = page_result(page, "th", lat, lon)
            if result:
                return result

    # 2) ค้นหา
    pages = api("th", generator="search", gsrsearch=name, gsrlimit=5,
                **PAGE_PROPS)
    for page in sorted(pages.values(), key=lambda p: p.get("index", 99)):
        ok = (accept(name, lat, lon, page)
              and "disambiguation" not in page.get("pageprops", {}))
        dbg(f"ค้นหา: {page.get('title')!r} -> {'รับ' if ok else 'ข้าม'}")
        if not ok:
            note(f"ค้นเจอ '{page.get('title')}' แต่ไม่ตรงชื่อ/พิกัด")
            continue
        result = page_result(page, "th", lat, lon)
        if result:
            return result
    return None


def commons_image(name, province, lat, lon):
    """ค้นไฟล์รูปบน Wikimedia Commons จากชื่อไทยในคำอธิบายรูป

    รับเมื่อ: ชื่อสถานที่อยู่ในชื่อ/คำอธิบายไฟล์ และ
    (พิกัดรูปห่างไม่เกิน 40 กม. หรือคำอธิบายมีชื่อจังหวัดด้วย)
    """
    pages = api("commons.wikimedia.org", generator="search", gsrnamespace=6,
                gsrsearch=name, gsrlimit=10, prop="imageinfo|coordinates",
                iiprop="url|mime|extmetadata", iiurlwidth=960,
                iiextmetadatafilter="ImageDescription|Artist|LicenseShortName",
                colimit=50)
    a, prov = norm(name), norm(province)
    for page in sorted(pages.values(), key=lambda p: p.get("index", 99)):
        info = (page.get("imageinfo") or [{}])[0]
        thumb = info.get("thumburl") or ""
        if (not thumb or info.get("mime") not in ("image/jpeg", "image/png")
                or SKIP.search(thumb)):
            continue
        meta = info.get("extmetadata", {})
        desc = re.sub(r"<[^>]+>", " ",
                      meta.get("ImageDescription", {}).get("value", ""))
        text = norm(page.get("title", "") + " " + desc)
        if a not in text:
            continue
        coords = page.get("coordinates")
        if coords and lat is not None and lon is not None:
            c = coords[0]
            if km(lat, lon, c["lat"], c["lon"]) > MAX_KM:
                continue
        elif prov not in text:
            continue
        artist = re.sub(r"<[^>]+>", "",
                        meta.get("Artist", {}).get("value", "")).strip()
        lic = meta.get("LicenseShortName", {}).get("value", "")
        credit = " / ".join(x for x in (artist[:80] or "ไม่ระบุ", lic) if x)
        dbg(f"commons: {page.get('title')!r}")
        return thumb, credit + " (Wikimedia Commons)", info.get("descriptionurl", "")
    return None


def find_image(name, province, lat, lon):
    return (wiki_image(name, lat, lon)
            or commons_image(name, province, lat, lon))


def check_connection():
    """ทดสอบว่าต่อ Wikipedia ได้ ก่อนเริ่มแก้ไฟล์"""
    try:
        r = session.get("https://th.wikipedia.org/w/api.php",
                        params={"action": "query", "format": "json",
                                "meta": "siteinfo"}, timeout=15)
        r.raise_for_status()
        return True, ""
    except requests.RequestException as error:
        return False, str(error)


def main():
    global DEBUG
    parser = argparse.ArgumentParser()
    parser.add_argument("--refresh", action="store_true",
                        help="ค้นหารูปใหม่ทุกแถว")
    parser.add_argument("--debug", metavar="ชื่อสถานที่",
                        help="ทดสอบสถานที่เดียว พร้อมแสดงรายละเอียดการค้น")
    args = parser.parse_args()

    print("fix_images.py v6 (หน่วงเวลา + ลองซ้ำเมื่อโดนจำกัดความถี่)")
    ok, error = check_connection()
    if not ok:
        print("ต่อ Wikipedia ไม่ได้ จึงยังไม่แก้ไฟล์ใด ๆ:", error)
        print("ตรวจอินเทอร์เน็ต / VPN / ไฟร์วอลล์ / proxy แล้วรันใหม่")
        return

    df = pd.read_csv(DATA, encoding="utf-8-sig").fillna("")
    for col in IMAGE_COLS:
        if col not in df.columns:
            df[col] = ""
        df[col] = df[col].astype(str).str.strip()
    lats = pd.to_numeric(df["lat"], errors="coerce")
    lons = pd.to_numeric(df["lon"], errors="coerce")

    if args.debug:
        DEBUG = True
        wanted = clean_name(args.debug)
        rows = df.index[df["name"].map(clean_name) == wanted]
        if len(rows) == 0:
            print(f"ไม่พบ '{wanted}' ใน places.csv (ต้องสะกดตรงกับคอลัมน์ name)")
            return
        i = rows[0]
        found = find_image(wanted, df.loc[i, "province"],
                           num(lats[i]), num(lons[i]))
        print("ผลลัพธ์:", found)
        if found:
            print("ลิงก์รูปเปิดได้:", check_url(found[0]))
        return

    shutil.copy(DATA, str(DATA) + ".bak")

    missing = []
    for i, row in df.iterrows():
        name = clean_name(row["name"])
        lat, lon = num(lats[i]), num(lons[i])
        current, credit = row["image_url"], row["image_credit"]
        if any((IMAGE_DIR / f"{row['name']}{e}").exists() for e in LOCAL_EXTS):
            print(f"[รูปที่เพิ่มเอง] {name}")
            continue
        unverified = "Openverse" in credit or "ทั่วไป" in credit
        if "/900px-" in current:  # ขนาด 900 ไม่ใช่ขนาดมาตรฐานของ Wikimedia
            upgraded = current.replace("/900px-", "/960px-")
            if url_ok(upgraded):
                current = upgraded
                df.loc[i, "image_url"] = upgraded

        if (not args.refresh and current and not unverified
                and url_ok(current)):
            print(f"[คงเดิม]   {name}")
            continue

        NOTES.clear()
        found = find_image(name, row["province"], lat, lon)
        if found:
            link_ok, detail = check_url(found[0])
            if not link_ok:
                print(f"[ลิงก์รูปเปิดไม่ได้] {name}: {detail}  {found[0]}")
                found = None

        if found:
            df.loc[i, IMAGE_COLS] = list(found)
            print(f"[ได้รูป]   {name}  <-  {found[1]}")
        elif current and not unverified and url_ok(current):
            print(f"[คงเดิม]   {name}")
        else:
            df.loc[i, IMAGE_COLS] = ["", "", ""]
            missing.append(f"{row['name']} ({row['province']})")
            reasons = "; ".join(dict.fromkeys(NOTES))[:160] or "ไม่พบบทความ"
            print(f"[ไม่มีรูป] {name}  ({reasons})")
        time.sleep(0.2)

    df.to_csv(DATA, index=False, encoding="utf-8-sig")
    print(f"\nเสร็จแล้ว: มีรูป {len(df) - len(missing)} / {len(df)} แห่ง")
    if missing:
        pd.DataFrame({"place": missing}).to_csv(
            DATA.parent / "missing_images.csv", index=False,
            encoding="utf-8-sig")
        print("ยังไม่มีรูป (บันทึกรายชื่อไว้ที่ data/missing_images.csv):")
        for m in missing:
            print(" -", m)


class Tee:
    """พิมพ์ทั้งหน้าจอและไฟล์ log"""

    def __init__(self, *streams):
        self.streams = streams

    def write(self, text):
        for stream in self.streams:
            stream.write(text)

    def flush(self):
        for stream in self.streams:
            stream.flush()


if __name__ == "__main__":
    with open(DATA.parent / "fix_images_log.txt", "w",
              encoding="utf-8") as log:
        sys.stdout = Tee(sys.__stdout__, log)
        try:
            main()
        finally:
            sys.stdout = sys.__stdout__