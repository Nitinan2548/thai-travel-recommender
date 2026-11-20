LABELS = {
    "th": {"title": "สรุปจุดเด่นของ", "good": "จุดเด่น", "warn": "ข้อควรระวัง",
           "time": "ช่วงเวลาที่เหมาะสม", "no_good": "ยังไม่มีข้อมูลจุดเด่น",
           "no_warn": "ยังไม่พบข้อควรระวังจากรีวิว", "no_time": "ยังไม่มีข้อมูลช่วงเวลา"},
    "en": {"title": "Highlights of", "good": "Highlights", "warn": "Things to watch out for",
           "time": "Best time to visit", "no_good": "No highlights available",
           "no_warn": "No cautions found in reviews", "no_time": "No timing information"},
    "zh": {"title": "亮点总结：", "good": "亮点", "warn": "注意事项",
           "time": "最佳游览时间", "no_good": "暂无亮点信息",
           "no_warn": "评价中未发现注意事项", "no_time": "暂无时间信息"},
}

TIME_WORDS = ["ควรมา", "ไปช่วง", "ช่วงเช้า", "ตอนเช้า", "ตอนเย็น", "ฤดู",
              "มกราคม", "กุมภาพันธ์", "มีนาคม", "เมษายน", "พฤษภาคม", "มิถุนายน",
              "กรกฎาคม", "สิงหาคม", "กันยายน", "ตุลาคม", "พฤศจิกายน", "ธันวาคม",
              "หน้าหนาว", "หน้าฝน", "หน้าร้อน"]

CAUTION_WORDS = ["เยอะ", "ระวัง", "โค้ง", "ร้อน", "แพง", "ฝนตก", "แออัด",
                 "ต้องแต่งกาย", "ต้องจอง", "รถติด", "อันตราย", "ลื่น", "ไกล"]


def _split_reviews(reviews):
    if not isinstance(reviews, str):
        return []
    return [r.strip() for r in reviews.split("|") if r.strip()]


def summarize_place(name, description, reviews, lang="th", tr=None):
    """tr(text) คืนคำแปลของข้อความไทยตามภาษาที่เลือก (ถ้าไม่มี คืนข้อความเดิม)"""
    L = LABELS.get(lang, LABELS["th"])

    def t(text):
        return tr(text) if (tr and lang != "th") else text

    time_tips, cautions, highlights = [], [], []

    for r in _split_reviews(reviews):
        if any(w in r for w in TIME_WORDS):
            time_tips.append(r)
        elif any(w in r for w in CAUTION_WORDS):
            cautions.append(r)
        else:
            highlights.append(r)

    if isinstance(description, str):
        for part in description.split():
            if len(highlights) >= 3:
                break
            if part not in highlights:
                highlights.append(part)

    sep = "" if lang == "zh" else " "
    lines = [f"**{L['title']}{sep}{t(name)}**", "", f"**{L['good']}**"]
    for h in highlights[:3]:
        lines.append(f"- {t(h)}")
    if not highlights:
        lines.append(f"- {L['no_good']}")

    lines += ["", f"**{L['warn']}**"]
    lines.append(f"- {t(cautions[0])}" if cautions else f"- {L['no_warn']}")

    lines += ["", f"**{L['time']}**"]
    lines.append(f"- {t(time_tips[0])}" if time_tips else f"- {L['no_time']}")

    return "\n".join(lines)