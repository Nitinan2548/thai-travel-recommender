from pathlib import Path

import pandas as pd
from pythainlp.tokenize import word_tokenize
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

DATA_DIR = Path(__file__).resolve().parent / "data"


def load_data(use_province_fallback=False):
    df = pd.read_csv(DATA_DIR / "places.csv", encoding="utf-8-sig")

    required = {"name", "province", "category", "description",
                "rating", "lat", "lon", "reviews"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError("places.csv ขาดคอลัมน์: " + ", ".join(sorted(missing)))

    for column in ("name", "province", "category", "description", "reviews",
                   "image_url", "image_credit", "image_source"):
        if column not in df.columns:
            df[column] = ""
        df[column] = df[column].fillna("").astype(str).str.strip()

    df["rating"] = pd.to_numeric(df["rating"], errors="coerce").fillna(0).clip(0, 5)
    for column in ("lat", "lon"):
        df[column] = pd.to_numeric(df[column], errors="coerce")
    df = df.dropna(subset=["lat", "lon"]).reset_index(drop=True)

    df["text"] = df["category"] + " " + df["description"]

    # รูปประจำจังหวัด (ไม่บังคับ): เติมเฉพาะแถวที่ image_url ว่าง
    province_path = DATA_DIR / "province_images.csv"
    if use_province_fallback and province_path.exists():
        pics = pd.read_csv(province_path, encoding="utf-8-sig").fillna("")
        if "province" in pics.columns:
            cols = ("image_url", "image_credit", "image_source")
            for c in cols:
                if c not in pics.columns:
                    pics[c] = ""
                pics[c] = pics[c].astype(str).str.strip()
            pics = pics.drop_duplicates("province").set_index("province")
            use_prov = df["image_url"].eq("")
            for c in cols:
                mapped = df["province"].map(pics[c]).fillna("")
                df.loc[use_prov, c] = mapped[use_prov]

    df["has_image"] = df["image_url"].str.startswith(("http://", "https://"))

    return df


def _tokenize(text):
    return [t for t in word_tokenize(text, engine="newmm") if t.strip()]


def recommend(df, query="", province=None, category=None,
              top_n=10, min_rating=0.0):
    """แนะนำสถานที่ท่องเที่ยวจากคำค้นหา

    - กรองตามจังหวัด / หมวดหมู่ / เรตติ้งขั้นต่ำ (ถ้าระบุ)
    - ถ้ามีคำค้นหา: จัดอันดับด้วย TF-IDF + cosine similarity ผสมกับเรตติ้ง
    - ถ้าไม่มีคำค้นหา: เรียงตามเรตติ้ง
    คืนค่า DataFrame ที่มีคอลัมน์ score เพิ่มเข้ามา
    """
    result = df.copy()

    if province and province not in ("ทั้งหมด", "All"):
        result = result[result["province"] == province]
    if category and category not in ("ทั้งหมด", "All"):
        result = result[result["category"] == category]
    if min_rating:
        result = result[result["rating"] >= min_rating]

    if result.empty:
        return result.assign(score=pd.Series(dtype=float))

    query = (query or "").strip()
    if not query:
        result = result.assign(score=result["rating"] / 5)
        return result.sort_values("score", ascending=False).head(top_n)

    vectorizer = TfidfVectorizer(tokenizer=_tokenize, token_pattern=None,
                                 lowercase=True)
    matrix = vectorizer.fit_transform(result["text"])
    query_vec = vectorizer.transform([query])
    similarity = cosine_similarity(query_vec, matrix).ravel()

    # ผสมความเกี่ยวข้อง 80% กับเรตติ้ง 20%
    score = 0.8 * similarity + 0.2 * (result["rating"].to_numpy() / 5)
    result = result.assign(score=score)
    return result.sort_values("score", ascending=False).head(top_n)
