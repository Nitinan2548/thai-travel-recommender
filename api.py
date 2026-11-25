import json
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


@app.get("/recommend")
def get_recommend(interest: str = "", province: str = "ทั้งหมด",
                  category: str = "ทั้งหมด", lang: str = "th", top: int = 5):
    res = recommend(df, interest, province or "ทั้งหมด",
                    category or "ทั้งหมด", top_n=min(top, 10))
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