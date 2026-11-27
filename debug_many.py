from recommender import load_data
from images import get_image_for_row, image_src

NAMES = ["ภูทับเบิก", "เขาค้อ", "อ่าวพังงา", "พระธาตุเชิงชุม",
         "มัสยิดกรือเซะ", "หาดชะอำ", "แพะเมืองผี", "เชียงคาน",
         "ทะเลน้อย", "ดอยอ่างขาง"]

df = load_data()
for _, r in df[df["name"].isin(NAMES)].iterrows():
    print("■", r["name"])
    print("   image_url:", repr(r["image_url"]))
    try:
        img = get_image_for_row(r)[0]
        src = image_src(img) if img else None
        print("   ได้รูป:", img)
        print("   src ยาว:", None if src is None else len(src), "ตัวอักษร")
    except Exception as e:
        print("   ERROR:", type(e).__name__, e)