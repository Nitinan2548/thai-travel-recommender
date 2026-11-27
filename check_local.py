import subprocess
from pathlib import Path

from PIL import Image

from images import get_image_for_row
from recommender import load_data

ROOT = Path(__file__).resolve().parent

# ไฟล์ที่ git ติดตามอยู่จริง (ถ้าไม่อยู่ในนี้ แปลว่าไม่ได้ขึ้น GitHub)
out = subprocess.run(["git", "-c", "core.quotepath=off", "ls-files"],
                     cwd=ROOT, capture_output=True, text=True, encoding="utf-8").stdout
tracked = set(out.splitlines())

df = load_data()
problems = []

for _, r in df.iterrows():
    name, prov = r["name"], r["province"]
    url = str(r["image_url"]).strip()
    why = []

    if not url:
        why.append("image_url ว่าง")
    elif url.startswith(("http://", "https://")):
        pass  # ลิงก์เว็บ ตรวจด้วย check_all_images.py
    else:
        if "\\" in url:
            why.append("พาธมี \\ (บนเว็บจริงต้องใช้ /)")
        p = ROOT / url.replace("\\", "/")
        if not p.exists():
            why.append("ไม่พบไฟล์ในเครื่อง")
        else:
            if p.name not in {x.name for x in p.parent.iterdir()}:
                why.append("ตัวพิมพ์เล็ก/ใหญ่ของชื่อไฟล์ไม่ตรง (เว็บจริงจะหาไม่เจอ)")
            try:
                with Image.open(p) as im:
                    im.verify()
            except Exception as e:
                why.append(f"ไฟล์เปิดเป็นรูปไม่ได้ ({type(e).__name__})")
            if url.replace("\\", "/") not in tracked:
                why.append("ไฟล์ไม่ได้อยู่ใน git (ยังไม่ได้ add/push)")

    try:
        if get_image_for_row(r)[0] is None:
            why.append("get_image_for_row คืนค่าไม่มีรูป")
    except Exception as e:
        why.append(f"get_image_for_row error ({type(e).__name__})")

    if why:
        problems.append((prov, name, url, why))

print(f"ตรวจ {len(df)} แห่ง พบปัญหา {len(problems)} แห่ง\n")
for prov, name, url, why in problems:
    print(f"■ {prov} / {name}")
    print(f"    image_url: {url!r}")
    for w in why:
        print("    -", w)