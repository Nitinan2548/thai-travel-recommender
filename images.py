"""หารูปของสถานที่ (ไม่ค้นรูปสดจากเน็ตอีกต่อไป เพื่อไม่ให้ได้รูปผิดที่)

ลำดับการหารูป:
  1. คอลัมน์ image_url ใน places.csv (เตรียมไว้ด้วย fix_images.py)
  2. ไฟล์รูปที่คุณใส่เองในโฟลเดอร์ data/images/ ตั้งชื่อไฟล์ให้ตรงกับชื่อสถานที่
     เช่น data/images/ดอยอินทนนท์.jpg

รูปที่แสดงในแอปเป็นสี่เหลี่ยมจัตุรัส 960x960 พิกเซล (ครอปจากกลางภาพ)
"""
import base64
import io
from functools import lru_cache
from pathlib import Path

from PIL import Image, ImageOps

IMAGE_DIR = Path(__file__).resolve().parent / "data" / "images"
EXTS = (".jpg", ".jpeg", ".png", ".webp")
SIZE = 960


def _local_image(name):
    for ext in EXTS:
        path = IMAGE_DIR / f"{name}{ext}"
        if path.exists():
            return str(path)
    return None


def get_image_for_row(row):
    """คืนค่า (image, credit, source_url) ถ้าไม่มีรูปคืน (None, None, None)"""
    url = str(row.get("image_url", "") or "").strip()
    if url.startswith(("http://", "https://")):
        credit = str(row.get("image_credit", "") or "").strip() or "ไม่ระบุ"
        source = str(row.get("image_source", "") or "").strip() or url
        return url, credit, source

    # พาธรูปในเครื่อง เช่น photos/doi.jpg (อิงจากโฟลเดอร์ของ images.py)
    if url:
        p = Path(url)
        if not p.is_absolute():
            p = Path(__file__).resolve().parent / url
        if p.exists():
            credit = str(row.get("image_credit", "") or "").strip() or "รูปที่เพิ่มเอง"
            source = str(row.get("image_source", "") or "").strip() or None
            return str(p), credit, source

    local = _local_image(str(row.get("name", "")).strip())
    if local:
        return local, "รูปที่เพิ่มเอง", None
    return None, None, None


@lru_cache(maxsize=256)
def _local_as_data_uri(path, mtime):
    """ครอปกลางภาพเป็น 960x960 แล้วแปลงเป็น data URI (mtime ไว้ให้แคชรู้ว่าไฟล์เปลี่ยน)"""
    with Image.open(path) as img:
        img = ImageOps.exif_transpose(img).convert("RGB")
        img = ImageOps.fit(img, (SIZE, SIZE), Image.LANCZOS)
        buffer = io.BytesIO()
        img.save(buffer, "JPEG", quality=85)
    return "data:image/jpeg;base64," + base64.b64encode(buffer.getvalue()).decode()


def image_src(image):
    """ค่า src สำหรับแท็ก <img>: ลิงก์เว็บใช้ได้เลย ไฟล์ในเครื่องแปลงเป็น 960x960"""
    if image.startswith(("http://", "https://")):
        return image
    path = Path(image)
    return _local_as_data_uri(str(path), path.stat().st_mtime)
