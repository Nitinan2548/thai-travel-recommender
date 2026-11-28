import json
import re
import unicodedata
from pathlib import Path

from fastapi import FastAPI

from recommender import load_data, recommend

app = FastAPI(title="Thai Travel API")
df = load_data()

TRANS_PATH = Path(__file__).resolve().parent / "data" / "translations.json"


def _norm(s):
    return "".join(unicodedata.normalize("NFC", str(s)).split())


TRANS = {}
if TRANS_PATH.exists():
    TRANS = {_norm(k): v for k, v in
             json.loads(TRANS_PATH.read_text(encoding="utf-8")).items()}


def tr(text, lang):
    if lang == "th":
        return text
    return TRANS.get(_norm(text), {}).get(lang) or text


# คำค้นอังกฤษ/จีน -> (คำค้นไทย, ประเภท)
KEYWORDS = {
    "cafe": ("คาเฟ่ ร้านกาแฟ", "คาเฟ่"), "coffee": ("คาเฟ่ ร้านกาแฟ", "คาเฟ่"),
    "咖啡": ("คาเฟ่ ร้านกาแฟ", "คาเฟ่"), "咖啡馆": ("คาเฟ่ ร้านกาแฟ", "คาเฟ่"),
    "sea": ("ทะเล ดำน้ำ", "ทะเล"), "beach": ("ทะเล หาดทราย", "ทะเล"),
    "island": ("เกาะ ทะเล", "ทะเล"), "diving": ("ดำน้ำ ทะเล", "ทะเล"),
    "海": ("ทะเล ดำน้ำ", "ทะเล"), "海边": ("ทะเล ดำน้ำ", "ทะเล"), "海岛": ("เกาะ ทะเล", "ทะเล"),
    "temple": ("วัด สถาปัตยกรรม", "วัด"), "wat": ("วัด", "วัด"),
    "寺庙": ("วัด สถาปัตยกรรม", "วัด"), "寺": ("วัด", "วัด"),
    "market": ("ตลาด ของฝาก", "ตลาด"), "shopping": ("ตลาด ของฝาก", "ตลาด"),
    "市场": ("ตลาด ของฝาก", "ตลาด"),
    "history": ("ประวัติศาสตร์ โบราณสถาน", "ประวัติศาสตร์"),
    "ruins": ("โบราณสถาน ประวัติศาสตร์", "ประวัติศาสตร์"),
    "historical": ("ประวัติศาสตร์ โบราณสถาน", "ประวัติศาสตร์"),
    "历史": ("ประวัติศาสตร์ โบราณสถาน", "ประวัติศาสตร์"),
    "古迹": ("โบราณสถาน ประวัติศาสตร์", "ประวัติศาสตร์"),
    "nature": ("ธรรมชาติ", "ธรรมชาติ"), "waterfall": ("น้ำตก ธรรมชาติ", "ธรรมชาติ"),
    "自然": ("ธรรมชาติ", "ธรรมชาติ"), "瀑布": ("น้ำตก ธรรมชาติ", "ธรรมชาติ"),
    "mountain": ("ภูเขา ทะเลหมอก อากาศเย็น", None),
    "山": ("ภูเขา ทะเลหมอก อากาศเย็น", None),
}

ALL = {"", "all", "ทั้งหมด", "全部", "none", "any"}


def interpret(interest, category):
    """คืน (คำค้นไทย, ประเภทที่กรอง)"""
    text = (interest or "").strip()
    cat = (category or "").strip()
    if cat.lower() in ALL:
        cat = "ทั้งหมด"

    low = text.lower()
    thai_parts, found_cat = [], None
    for key, (th, c) in KEYWORDS.items():
        if (key.isascii() and re.search(rf"\b{re.escape(key)}\b", low)) or \
           (not key.isascii() and key in text):
            thai_parts.append(th)
            found_cat = found_cat or c

    if thai_parts:
        query = " ".join(thai_parts)
        if cat == "ทั้งหมด" and found_cat:
            cat = found_cat
        return query, cat
    return text, cat


@app.get("/recommend")
def get_recommend(interest: str = "", province: str = "ทั้งหมด",
                  category: str = "ทั้งหมด", lang: str = "th", top: int = 5):
    query, cat = interpret(interest, category)
    prov = (province or "").strip()
    if prov.lower() in ALL:
        prov = "ทั้งหมด"

    res = recommend(df, query, prov, cat, top_n=min(top, 10))
    out = []
    for _, r in res.iterrows():
        out.append({
            "name": tr(r["name"], lang),
            "province": r["province"],
            "category": r["category"],
            "rating": float(r["rating"]),
            "description": tr(r["description"], lang),
            "lat": float(r["lat"]),
            "lon": float(r["lon"]),
        })
    return {"count": len(out), "results": out}


@app.get("/health")
def health():
    return {"ok": True, "places": len(df)}