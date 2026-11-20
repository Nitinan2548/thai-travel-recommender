import time
import requests
import pandas as pd

HEADERS = {
    "User-Agent": "ThaiTravelRecommender/1.0 (student project)"
}

PROVINCE_QUERY = {
    "กรุงเทพมหานคร": "Bangkok Thailand landmark",
    "เชียงใหม่": "Chiang Mai Thailand temple mountain",
    "เชียงราย": "Chiang Rai Thailand temple",
    "แม่ฮ่องสอน": "Mae Hong Son Thailand mountain",
    "ลำปาง": "Lampang Thailand temple",
    "ลำพูน": "Lamphun Thailand temple",
    "น่าน": "Nan Thailand Thailand temple",
    "แพร่": "Phrae Thailand",
    "พะเยา": "Phayao Thailand lake",
    "ตาก": "Tak Thailand waterfall",
    "สุโขทัย": "Sukhothai Thailand historical park",
    "พิษณุโลก": "Phitsanulok Thailand temple",
    "กำแพงเพชร": "Kamphaeng Phet Thailand historical park",
    "อุตรดิตถ์": "Uttaradit Thailand",
    "พิจิตร": "Phichit Thailand",
    "เพชรบูรณ์": "Phetchabun Thailand mountain",
    "นครสวรรค์": "Nakhon Sawan Thailand",
    "อุทัยธานี": "Uthai Thani Thailand",
    "ชัยนาท": "Chai Nat Thailand",
    "ลพบุรี": "Lopburi Thailand temple",
    "สิงห์บุรี": "Sing Buri Thailand",
    "อ่างทอง": "Ang Thong Thailand",
    "สระบุรี": "Saraburi Thailand temple",
    "พระนครศรีอยุธยา": "Ayutthaya Thailand historical park",
    "สุพรรณบุรี": "Suphan Buri Thailand",
    "นครปฐม": "Nakhon Pathom Thailand pagoda",
    "นนทบุรี": "Nonthaburi Thailand",
    "ปทุมธานี": "Pathum Thani Thailand",
    "สมุทรปราการ": "Samut Prakan Thailand",
    "สมุทรสาคร": "Samut Sakhon Thailand",
    "สมุทรสงคราม": "Samut Songkhram Thailand floating market",
    "ราชบุรี": "Ratchaburi Thailand floating market",
    "กาญจนบุรี": "Kanchanaburi Thailand bridge river Kwai",
    "เพชรบุรี": "Phetchaburi Thailand palace",
    "ประจวบคีรีขันธ์": "Prachuap Khiri Khan Thailand beach",
    "นครนายก": "Nakhon Nayok Thailand waterfall",
    "ปราจีนบุรี": "Prachinburi Thailand national park",
    "ฉะเชิงเทรา": "Chachoengsao Thailand temple",
    "ชลบุรี": "Chonburi Thailand beach",
    "ระยอง": "Rayong Thailand beach",
    "จันทบุรี": "Chanthaburi Thailand",
    "ตราด": "Trat Thailand island",
    "สระแก้ว": "Sa Kaeo Thailand",
    "นครราชสีมา": "Nakhon Ratchasima Thailand national park",
    "บุรีรัมย์": "Buriram Thailand castle",
    "สุรินทร์": "Surin Thailand",
    "ศรีสะเกษ": "Sisaket Thailand",
    "อุบลราชธานี": "Ubon Ratchathani Thailand",
    "ยโสธร": "Yasothon Thailand",
    "ชัยภูมิ": "Chaiyaphum Thailand",
    "อำนาจเจริญ": "Amnat Charoen Thailand",
    "หนองบัวลำภู": "Nong Bua Lamphu Thailand",
    "ขอนแก่น": "Khon Kaen Thailand",
    "อุดรธานี": "Udon Thani Thailand lotus lake",
    "เลย": "Loei Thailand mountain",
    "หนองคาย": "Nong Khai Thailand Mekong",
    "มหาสารคาม": "Maha Sarakham Thailand",
    "ร้อยเอ็ด": "Roi Et Thailand",
    "กาฬสินธุ์": "Kalasin Thailand",
    "สกลนคร": "Sakon Nakhon Thailand",
    "นครพนม": "Nakhon Phanom Thailand Mekong",
    "มุกดาหาร": "Mukdahan Thailand Mekong",
    "บึงกาฬ": "Bueng Kan Thailand",
    "นครศรีธรรมราช": "Nakhon Si Thammarat Thailand temple",
    "กระบี่": "Krabi Thailand beach",
    "พังงา": "Phang Nga Thailand bay",
    "ภูเก็ต": "Phuket Thailand beach",
    "สุราษฎร์ธานี": "Surat Thani Thailand island",
    "ระนอง": "Ranong Thailand",
    "ชุมพร": "Chumphon Thailand beach",
    "สงขลา": "Songkhla Thailand lake",
    "สตูล": "Satun Thailand island",
    "ตรัง": "Trang Thailand beach",
    "พัทลุง": "Phatthalung Thailand lotus lake",
    "ปัตตานี": "Pattani Thailand",
    "ยะลา": "Yala Thailand",
    "นราธิวาส": "Narathiwat Thailand",
}


def get_first_image(query):
    response = requests.get(
        "https://api.openverse.org/v1/images/",
        params={
            "q": query,
            "page_size": 10,
            "mature": "false",
            "license_type": "all-cc",
        },
        headers=HEADERS,
        timeout=15,
    )

    if response.status_code != 200:
        return None

    for item in response.json().get("results", []):
        url = item.get("thumbnail") or item.get("url")
        if not url:
            continue

        creator = item.get("creator") or "ไม่ระบุ"
        license_name = (item.get("license") or "").upper()
        credit = f"{creator} / {license_name} (Openverse)"

        return {
            "image_url": url,
            "image_credit": credit,
            "image_source": item.get("foreign_landing_url") or "",
        }

    return None


def main():
    rows = []

    for province, query in PROVINCE_QUERY.items():
        image = get_first_image(query)

        if image:
            rows.append({
                "province": province,
                **image,
            })
            print(f"OK: {province}")
        else:
            rows.append({
                "province": province,
                "image_url": "",
                "image_credit": "",
                "image_source": "",
            })
            print(f"ไม่พบรูป: {province}")

        time.sleep(0.4)

    pd.DataFrame(rows).to_csv(
        "data/province_images.csv",
        index=False,
        encoding="utf-8-sig",
    )


if __name__ == "__main__":
    main()