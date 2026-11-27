import json
import unicodedata
from pathlib import Path

import streamlit as st
import folium
from streamlit_folium import st_folium

from recommender import load_data, recommend
from summarizer import summarize_place
from images import get_image_for_row

st.set_page_config(page_title="Thai Travel", page_icon="🏝️", layout="wide")

# ---------- ข้อความส่วนติดต่อผู้ใช้ ----------
TEXT = {
    "th": {
        "lang_label": "ภาษา / Language / 语言",
        "title": "แนะนำที่เที่ยวไทย",
        "subtitle": "ค้นหาแหล่งท่องเที่ยวตามความสนใจ พร้อมสรุปจุดเด่น รูปประกอบ และแผนที่",
        "places": "สถานที่", "provinces": "จังหวัด", "sorted_by": "เรียงตามความตรงใจ",
        "sidebar_head": "เลือกสิ่งที่คุณชอบ", "quick": "ทางลัดความสนใจ",
        "q_sea": "ทะเล", "q_mountain": "ภูเขา", "q_temple": "วัด", "q_cafe": "คาเฟ่",
        "interest": "ความสนใจ (เว้นว่างได้)",
        "placeholder": "เช่น ทะเล ดำน้ำ อากาศเย็น",
        "interest_note": "",
        "province": "จังหวัด", "category": "ประเภท", "all": "ทั้งหมด",
        "search": "ค้นหา",
        "welcome_title": "พร้อมออกเดินทางหรือยัง?",
        "welcome_body": "เลือกทางลัด หรือพิมพ์ความสนใจที่แถบด้านซ้าย แล้วกด <b>ค้นหา</b><br>เว้นว่างไว้ก็ได้ ระบบจะแสดงสถานที่คะแนนสูงสุดให้",
        "no_cat": "ไม่มี \"{cat}\" ในจังหวัด{prov} ตามข้อมูลที่มี",
        "cats_in_prov": "ประเภทที่มีในจังหวัดนี้: ",
        "shown_instead": "สถานที่ประเภทเดียวกันในจังหวัดอื่น (แสดงแทน)",
        "recommend": "แนะนำ {n} แห่ง", "interest_is": "ความสนใจ: ", "general": "ทั่วไป",
        "map": "แผนที่",
        "load_fail": "โหลดข้อมูลไม่สำเร็จ: ", "no_data": "ยังไม่มีข้อมูลสถานที่",
        "data_note": "",
    },
    "en": {
        "lang_label": "ภาษา / Language / 语言",
        "title": "Discover Thailand",
        "subtitle": "Find places by interest, with highlights, photos and a map",
        "places": "places", "provinces": "provinces", "sorted_by": "Ranked by relevance",
        "sidebar_head": "Choose what you like", "quick": "Quick picks",
        "q_sea": "Sea", "q_mountain": "Mountain", "q_temple": "Temple", "q_cafe": "Cafe",
        "interest": "Interest (optional)",
        "placeholder": "e.g. ทะเล ดำน้ำ อากาศเย็น",
        "interest_note": "Tip: search keywords must be in Thai. Leave empty to see top-rated places.",
        "province": "Province", "category": "Category", "all": "All",
        "search": "Search",
        "welcome_title": "Ready to travel?",
        "welcome_body": "Pick a quick option or set filters on the left, then press <b>Search</b><br>You can leave the interest empty to see top-rated places",
        "no_cat": "No \"{cat}\" places in {prov} in our data",
        "cats_in_prov": "Categories available in this province: ",
        "shown_instead": "Same category in other provinces (shown instead)",
        "recommend": "{n} recommended places", "interest_is": "Interest: ", "general": "general",
        "map": "Map",
        "load_fail": "Failed to load data: ", "no_data": "No place data yet",
        "data_note": "Descriptions and highlights were translated from Thai by an AI assistant.",
    },
    "zh": {
        "lang_label": "ภาษา / Language / 语言",
        "title": "泰国旅游推荐",
        "subtitle": "按兴趣查找景点，附亮点总结、图片和地图",
        "places": "个景点", "provinces": "个府", "sorted_by": "按匹配度排序",
        "sidebar_head": "选择您的喜好", "quick": "快捷选择",
        "q_sea": "海边", "q_mountain": "山", "q_temple": "寺庙", "q_cafe": "咖啡馆",
        "interest": "兴趣（可留空）",
        "placeholder": "例如 ทะเล ดำน้ำ อากาศเย็น",
        "interest_note": "提示：搜索关键词需用泰语输入。留空则显示评分最高的景点。",
        "province": "府", "category": "类别", "all": "全部",
        "search": "搜索",
        "welcome_title": "准备好出发了吗？",
        "welcome_body": "选择快捷选项或在左侧设置筛选条件，然后点击<b>搜索</b><br>兴趣可留空，系统将显示评分最高的景点",
        "no_cat": "数据中 {prov} 没有“{cat}”景点",
        "cats_in_prov": "该府现有类别：",
        "shown_instead": "显示其他府的同类景点",
        "recommend": "为您推荐 {n} 个景点", "interest_is": "兴趣：", "general": "通用",
        "map": "地图",
        "load_fail": "数据加载失败：", "no_data": "暂无景点数据",
        "data_note": "景点介绍与亮点由 AI 助手从泰语翻译而成。",
    },
}

CAT_NAMES = {
    "th": {"ธรรมชาติ": "ธรรมชาติ", "วัด": "วัด", "ทะเล": "ทะเล",
           "คาเฟ่": "คาเฟ่", "ตลาด": "ตลาด", "ประวัติศาสตร์": "ประวัติศาสตร์"},
    "en": {"ธรรมชาติ": "Nature", "วัด": "Temple", "ทะเล": "Sea & Islands",
           "คาเฟ่": "Cafe", "ตลาด": "Market", "ประวัติศาสตร์": "History"},
    "zh": {"ธรรมชาติ": "自然", "วัด": "寺庙", "ทะเล": "海岛海滩",
           "คาเฟ่": "咖啡馆", "ตลาด": "市场", "ประวัติศาสตร์": "历史古迹"},
}

PROVINCE_EN = {
    "กรุงเทพมหานคร": "Bangkok", "เชียงใหม่": "Chiang Mai", "เชียงราย": "Chiang Rai",
    "แม่ฮ่องสอน": "Mae Hong Son", "ลำปาง": "Lampang", "ลำพูน": "Lamphun",
    "น่าน": "Nan", "แพร่": "Phrae", "พะเยา": "Phayao", "ตาก": "Tak",
    "สุโขทัย": "Sukhothai", "พิษณุโลก": "Phitsanulok", "กำแพงเพชร": "Kamphaeng Phet",
    "อุตรดิตถ์": "Uttaradit", "พิจิตร": "Phichit", "เพชรบูรณ์": "Phetchabun",
    "นครสวรรค์": "Nakhon Sawan", "อุทัยธานี": "Uthai Thani", "ชัยนาท": "Chai Nat",
    "ลพบุรี": "Lopburi", "สิงห์บุรี": "Sing Buri", "อ่างทอง": "Ang Thong",
    "สระบุรี": "Saraburi", "พระนครศรีอยุธยา": "Ayutthaya", "สุพรรณบุรี": "Suphan Buri",
    "นครปฐม": "Nakhon Pathom", "นนทบุรี": "Nonthaburi", "ปทุมธานี": "Pathum Thani",
    "สมุทรปราการ": "Samut Prakan", "สมุทรสาคร": "Samut Sakhon",
    "สมุทรสงคราม": "Samut Songkhram", "ราชบุรี": "Ratchaburi", "กาญจนบุรี": "Kanchanaburi",
    "เพชรบุรี": "Phetchaburi", "ประจวบคีรีขันธ์": "Prachuap Khiri Khan",
    "นครนายก": "Nakhon Nayok", "ปราจีนบุรี": "Prachinburi", "ฉะเชิงเทรา": "Chachoengsao",
    "ชลบุรี": "Chonburi", "ระยอง": "Rayong", "จันทบุรี": "Chanthaburi",
    "ตราด": "Trat", "สระแก้ว": "Sa Kaeo", "นครราชสีมา": "Nakhon Ratchasima",
    "บุรีรัมย์": "Buriram", "สุรินทร์": "Surin", "ศรีสะเกษ": "Sisaket",
    "อุบลราชธานี": "Ubon Ratchathani", "ยโสธร": "Yasothon", "ชัยภูมิ": "Chaiyaphum",
    "อำนาจเจริญ": "Amnat Charoen", "หนองบัวลำภู": "Nong Bua Lamphu", "ขอนแก่น": "Khon Kaen",
    "อุดรธานี": "Udon Thani", "เลย": "Loei", "หนองคาย": "Nong Khai",
    "มหาสารคาม": "Maha Sarakham", "ร้อยเอ็ด": "Roi Et", "กาฬสินธุ์": "Kalasin",
    "สกลนคร": "Sakon Nakhon", "นครพนม": "Nakhon Phanom", "มุกดาหาร": "Mukdahan",
    "บึงกาฬ": "Bueng Kan", "นครศรีธรรมราช": "Nakhon Si Thammarat", "กระบี่": "Krabi",
    "พังงา": "Phang Nga", "ภูเก็ต": "Phuket", "สุราษฎร์ธานี": "Surat Thani",
    "ระนอง": "Ranong", "ชุมพร": "Chumphon", "สงขลา": "Songkhla", "สตูล": "Satun",
    "ตรัง": "Trang", "พัทลุง": "Phatthalung", "ปัตตานี": "Pattani",
    "ยะลา": "Yala", "นราธิวาส": "Narathiwat",
}

PROVINCE_ZH = {
    "กรุงเทพมหานคร": "曼谷", "เชียงใหม่": "清迈", "เชียงราย": "清莱",
    "แม่ฮ่องสอน": "夜丰颂", "ลำปาง": "南邦", "ลำพูน": "南奔",
    "น่าน": "难", "แพร่": "帕", "พะเยา": "帕尧", "ตาก": "达",
    "สุโขทัย": "素可泰", "พิษณุโลก": "彭世洛", "กำแพงเพชร": "甘烹碧",
    "อุตรดิตถ์": "程逸", "พิจิตร": "披集", "เพชรบูรณ์": "碧差汶",
    "นครสวรรค์": "北榄坡", "อุทัยธานี": "乌泰他尼", "ชัยนาท": "猜纳",
    "ลพบุรี": "华富里", "สิงห์บุรี": "信武里", "อ่างทอง": "红统",
    "สระบุรี": "北标", "พระนครศรีอยุธยา": "大城", "สุพรรณบุรี": "素攀武里",
    "นครปฐม": "佛统", "นนทบุรี": "暖武里", "ปทุมธานี": "巴吞他尼",
    "สมุทรปราการ": "北榄府", "สมุทรสาคร": "龙仔厝",
    "สมุทรสงคราม": "夜功", "ราชบุรี": "叻丕", "กาญจนบุรี": "北碧",
    "เพชรบุรี": "碧武里", "ประจวบคีรีขันธ์": "巴蜀",
    "นครนายก": "那空那育", "ปราจีนบุรี": "巴真武里", "ฉะเชิงเทรา": "北柳",
    "ชลบุรี": "春武里", "ระยอง": "罗勇", "จันทบุรี": "尖竹汶",
    "ตราด": "桐艾", "สระแก้ว": "沙缴", "นครราชสีมา": "呵叻",
    "บุรีรัมย์": "武里南", "สุรินทร์": "素林", "ศรีสะเกษ": "四色菊",
    "อุบลราชธานี": "乌汶", "ยโสธร": "耶梭通", "ชัยภูมิ": "猜也奔",
    "อำนาจเจริญ": "安纳乍能", "หนองบัวลำภู": "廊磨南蒲", "ขอนแก่น": "孔敬",
    "อุดรธานี": "乌隆", "เลย": "黎", "หนองคาย": "廊开",
    "มหาสารคาม": "玛哈沙拉堪", "ร้อยเอ็ด": "黎逸", "กาฬสินธุ์": "加拉信",
    "สกลนคร": "色军", "นครพนม": "那空帕农", "มุกดาหาร": "穆达汉",
    "บึงกาฬ": "汶干", "นครศรีธรรมราช": "那空是贪玛叻", "กระบี่": "甲米",
    "พังงา": "攀牙", "ภูเก็ต": "普吉", "สุราษฎร์ธานี": "素叻他尼",
    "ระนอง": "拉廊", "ชุมพร": "春蓬", "สงขลา": "宋卡", "สตูล": "沙敦",
    "ตรัง": "董里", "พัทลุง": "博他仑", "ปัตตานี": "北大年",
    "ยะลา": "惹拉", "นราธิวาส": "那拉提瓦",
}

PROV_NAMES = {"en": PROVINCE_EN, "zh": PROVINCE_ZH}

ICON = {"ธรรมชาติ": "🌿", "วัด": "🛕", "ทะเล": "🏖️",
        "คาเฟ่": "☕", "ตลาด": "🛍️", "ประวัติศาสตร์": "🏛️"}


def _norm(s):
    """ทำความสะอาดอักขระ + ตัดช่องว่าง ใช้เทียบข้อความเท่านั้น"""
    return "".join(unicodedata.normalize("NFC", str(s)).split())


# ---------- คำแปลเนื้อหา (จาก merge_translations.py) ----------
TRANS_PATH = Path(__file__).resolve().parent / "data" / "translations.json"


@st.cache_data(show_spinner=False)
def load_translations(mtime):
    """mtime ทำให้แคชรีเฟรชเองเมื่อไฟล์คำแปลเปลี่ยน"""
    if TRANS_PATH.exists():
        try:
            raw = json.loads(TRANS_PATH.read_text(encoding="utf-8"))
            return {_norm(k): v for k, v in raw.items()}
        except Exception:
            return {}
    return {}


_mtime = TRANS_PATH.stat().st_mtime if TRANS_PATH.exists() else 0
TRANS = load_translations(_mtime)

# ---------- เลือกภาษา ----------
LANGS = {"ไทย": "th", "English": "en", "中文": "zh"}
if "lang_name" not in st.session_state:
    st.session_state["lang_name"] = "ไทย"

with st.sidebar:
    st.radio(TEXT["th"]["lang_label"], list(LANGS.keys()),
             key="lang_name", horizontal=True)

lang = LANGS[st.session_state["lang_name"]]
T = TEXT[lang]


def tr(text):
    """แปลข้อความไทยเป็นภาษาที่เลือก ถ้าไม่มีคำแปลให้คืนข้อความเดิม"""
    if lang == "th":
        return text
    return TRANS.get(_norm(text), {}).get(lang) or text


def cat_label(c):
    if c == "ทั้งหมด":
        return T["all"]
    return f"{ICON.get(c, '📌')} {CAT_NAMES[lang].get(c, c)}"


def prov_label(p):
    if p == "ทั้งหมด":
        return T["all"]
    if lang == "th":
        return p
    return PROV_NAMES[lang].get(p, p)


# ---------- สไตล์ ----------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Prompt:wght@400;500;600;700&family=Noto+Sans+SC:wght@400;500;700&display=swap');
html, body, [class*="css"], .stMarkdown, button, input, label {
    font-family: 'Prompt', 'Noto Sans SC', sans-serif !important;
}
.block-container {padding-top: 1.5rem; max-width: 1400px;}
#MainMenu, footer {visibility: hidden;}
.hero {
    background: linear-gradient(120deg, #0B5F68 0%, #0E7C86 45%, #4FB3BF 100%);
    border-radius: 22px; padding: 2.2rem 2.4rem; color: #fff;
    box-shadow: 0 10px 30px rgba(14,124,134,0.25);
    position: relative; overflow: hidden; margin-bottom: 1.4rem;
}
.hero::after {content: "🌴"; position: absolute; right: 2rem; bottom: -1rem;
    font-size: 7rem; opacity: 0.18;}
.hero h1 {margin: 0; font-size: 2.3rem; font-weight: 700; color: #fff !important;}
.hero p {margin: 0.5rem 0 0 0; font-size: 1.05rem; opacity: 0.95;}
.badges {margin-top: 1rem;}
.badge {display: inline-block; background: rgba(255,255,255,0.2);
    border: 1px solid rgba(255,255,255,0.35); border-radius: 999px;
    padding: 0.25rem 0.9rem; margin-right: 0.5rem; font-size: 0.9rem;}
section[data-testid="stSidebar"] {border-right: 1px solid #CFE6E9;}
section[data-testid="stSidebar"] h2 {color: #0E7C86; font-weight: 700;}
div[data-testid="stForm"] {background: #FFFFFF; border: 1px solid #CFE6E9;
    border-radius: 16px; box-shadow: 0 4px 14px rgba(14,124,134,0.08);}
.stButton > button, div[data-testid="stFormSubmitButton"] > button {
    border-radius: 12px; font-weight: 600; border: none;
    transition: transform .15s, box-shadow .15s;}
.stButton > button:hover, div[data-testid="stFormSubmitButton"] > button:hover {
    transform: translateY(-2px); box-shadow: 0 6px 14px rgba(14,124,134,0.3);}
div[data-testid="stExpander"] {
    border-radius: 18px !important; border: 1px solid #CFE6E9 !important;
    background: #FFFFFF; box-shadow: 0 4px 16px rgba(14,124,134,0.10);
    margin-bottom: 0.9rem; overflow: hidden; transition: box-shadow .2s;}
div[data-testid="stExpander"]:hover {box-shadow: 0 8px 24px rgba(14,124,134,0.20);}
div[data-testid="stExpander"] summary {font-weight: 600; font-size: 1.02rem;}
div[data-testid="stImage"] img {border-radius: 14px; width: 100%; max-height: 420px; object-fit: cover;}
.tag {display: inline-block; padding: 0.2rem 0.8rem; border-radius: 999px;
    font-size: 0.85rem; font-weight: 600; margin-right: 0.4rem;}
.tag-cat {background: #DFF1F3; color: #0B5F68;}
.tag-prov {background: #FFF1D6; color: #8A5A00;}
.tag-rate {background: #FFE9B8; color: #7A4B00;}
.result-head {font-size: 1.25rem; font-weight: 700; color: #0B5F68; margin: 0.2rem 0 0.8rem 0;}
.result-head span {color: #6B8A90; font-weight: 400; font-size: 0.95rem;}
.welcome {background: #FFFFFF; border: 2px dashed #9FD0D6; border-radius: 20px;
    padding: 2.5rem; text-align: center; color: #3E6A72;}
.welcome .big {font-size: 3rem;}
</style>
""", unsafe_allow_html=True)

# ---------- โหลดข้อมูล ----------
try:
    df = load_data()
except Exception as error:
    st.error(f"{T['load_fail']}{error}")
    st.stop()

if df.empty:
    st.warning(T["no_data"])
    st.stop()

n_places, n_prov = len(df), df["province"].nunique()

# ---------- แบนเนอร์ ----------
st.markdown(f"""
<div class="hero">
  <h1>🏝️ {T['title']}</h1>
  <p>{T['subtitle']}</p>
  <div class="badges">
    <span class="badge">📍 {n_places} {T['places']}</span>
    <span class="badge">🗺️ {n_prov} {T['provinces']}</span>
    <span class="badge">⭐ {T['sorted_by']}</span>
  </div>
</div>
""", unsafe_allow_html=True)

# ---------- แถบด้านข้าง ----------
provinces = ["ทั้งหมด"] + sorted(v for v in df["province"].unique() if v.strip())
categories = ["ทั้งหมด"] + sorted(v for v in df["category"].unique() if v.strip())

with st.sidebar:
    st.header(f"🧭 {T['sidebar_head']}")

    st.caption(T["quick"])
    q1, q2 = st.columns(2)
    quick = None
    if q1.button(f"🏖️ {T['q_sea']}", use_container_width=True):
        quick = "ทะเล ดำน้ำ"
    if q2.button(f"⛰️ {T['q_mountain']}", use_container_width=True):
        quick = "ภูเขา ทะเลหมอก อากาศเย็น"
    if q1.button(f"🛕 {T['q_temple']}", use_container_width=True):
        quick = "วัด สถาปัตยกรรม"
    if q2.button(f"☕ {T['q_cafe']}", use_container_width=True):
        quick = "คาเฟ่ ถ่ายรูป"

    with st.form("search_form"):
        interest = st.text_input(T["interest"], placeholder=T["placeholder"])
        if T["interest_note"]:
            st.caption(T["interest_note"])
        province = st.selectbox(T["province"], provinces, format_func=prov_label)
        category = st.selectbox(T["category"], categories, format_func=cat_label)
        submitted = st.form_submit_button(f"🔍 {T['search']}", type="primary",
                                          use_container_width=True)

if quick:
    st.session_state["query"] = (quick, "ทั้งหมด", "ทั้งหมด")
elif submitted:
    st.session_state["query"] = (interest, province, category)

query = st.session_state.get("query")

# ---------- หน้าแรก ----------
if query is None:
    st.markdown(f"""
    <div class="welcome">
      <div class="big">🧳🌏✈️</div>
      <h3>{T['welcome_title']}</h3>
      <p>{T['welcome_body']}</p>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

# ---------- ค้นหา ----------
q_interest, q_province, q_category = query
results = recommend(df, q_interest, q_province, q_category)

if results.empty:
    cat_plain = CAT_NAMES[lang].get(q_category, q_category)
    st.warning(T["no_cat"].format(cat=cat_plain, prov=prov_label(q_province)))
    in_prov = df[df["province"] == q_province]
    if not in_prov.empty:
        st.info(T["cats_in_prov"] + ", ".join(
            CAT_NAMES[lang].get(c, c) for c in sorted(in_prov["category"].unique())))
    st.caption(T["shown_instead"])
    results = recommend(df, q_interest, "ทั้งหมด", q_category)

if results.empty:
    st.stop()

# ---------- ผลลัพธ์ ----------
col1, col2 = st.columns([1.1, 1])

with col1:
    label = q_interest.strip() if q_interest.strip() else T["general"]
    st.markdown(
        f'<div class="result-head">✨ {T["recommend"].format(n=len(results))} '
        f'<span>{T["interest_is"]}{label}</span></div>', unsafe_allow_html=True)
    if T["data_note"]:
        st.caption(T["data_note"])

    for i, (_, row) in enumerate(results.iterrows(), start=1):
        icon = ICON.get(row["category"], "📌")
        cat_txt = CAT_NAMES[lang].get(row["category"], row["category"])
        prov_txt = prov_label(row["province"])
        name_txt = tr(row["name"])
        with st.expander(f"{i}. {icon} {name_txt}  ·  {prov_txt}  ·  ⭐ {row['rating']}",
                         expanded=(i == 1)):
            img_url, credit, src_url = get_image_for_row(row)
            if img_url:
                st.image(img_url, use_container_width=True)

            st.markdown(
                f'<span class="tag tag-cat">{icon} {cat_txt}</span>'
                f'<span class="tag tag-prov">📍 {prov_txt}</span>'
                f'<span class="tag tag-rate">⭐ {row["rating"]}</span>',
                unsafe_allow_html=True)
            st.write("")
            st.write(tr(row["description"]))
            st.divider()
            st.markdown(summarize_place(
                row["name"], row["description"], row["reviews"],
                lang=lang, tr=tr))

with col2:
    st.markdown(f'<div class="result-head">🗺️ {T["map"]}</div>', unsafe_allow_html=True)

    m = folium.Map(location=[results["lat"].mean(), results["lon"].mean()],
                   zoom_start=6, tiles="OpenStreetMap")

    for i, (_, row) in enumerate(results.iterrows(), start=1):
        folium.CircleMarker(
            [row["lat"], row["lon"]], radius=11, color="#FFFFFF", weight=2,
            fill=True, fill_color="#0E7C86", fill_opacity=0.95,
            tooltip=f"{i}. {tr(row['name'])} ({prov_label(row['province'])})",
        ).add_to(m)

    lat_span = results["lat"].max() - results["lat"].min()
    lon_span = results["lon"].max() - results["lon"].min()

    if len(results) == 1 or (lat_span < 0.02 and lon_span < 0.02):
        m.location = [results["lat"].mean(), results["lon"].mean()]
        m.options["zoom"] = 12
    else:
        m.fit_bounds([[results["lat"].min(), results["lon"].min()],
                      [results["lat"].max(), results["lon"].max()]],
                     padding=(30, 30))

    st_folium(m, height=520, width=None, returned_objects=[])