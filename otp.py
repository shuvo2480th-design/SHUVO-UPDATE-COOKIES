import requests, time, telebot, pickle, os, re, threading, random
from telebot import types
from flask import Flask

# --- CONFIG ---
BOT_TOKEN_1 = "8658807204:AAHuvlFfHgb19m1wKHkJbeyYcf-50SuaMi8"
BOT_TOKEN_2 = "8764978166:AAEhHy4R82VK9FmygIyPAQaNxtYVfbx-eXY"
CHANNEL_ID = "-1002670575248"
API_KEY = "MUBTR1MKUBO"
PANEL_BOT_URL = "https://t.me/shuvo_number_bot"
RANGE_CHANNEL_URL = "https://t.me/range_channele"

bot1 = telebot.TeleBot(BOT_TOKEN_1)
bot2 = telebot.TeleBot(BOT_TOKEN_2)
DB_FILE = "otp_history.pkl"

def get_country_info(number):
    countries_map = {
        "93": "Afghanistan 🇦🇫", "355": "Albania 🇦🇱", "213": "Algeria 🇩🇿", "376": "Andorra 🇦🇩", "244": "Angola 🇦🇴", "1268": "Antigua and Barbuda 🇦🇬", "54": "Argentina 🇦🇷", "374": "Armenia 🇦🇲", "61": "Australia 🇦🇺", "43": "Austria 🇦🇹", "994": "Azerbaijan 🇦🇿",
        "1242": "Bahamas 🇧🇸", "973": "Bahrain 🇧🇭", "880": "Bangladesh 🇧🇩", "1246": "Barbados 🇧🇧", "375": "Belarus 🇧🇾", "32": "Belgium 🇧🇪", "501": "Belize 🇧🇿", "229": "Benin 🇧🇯", "975": "Bhutan 🇧🇹", "591": "Bolivia 🇧🇴", "387": "Bosnia and Herzegovina 🇧🇦", "267": "Botswana 🇧🇼", "55": "Brazil 🇧🇷", "673": "Brunei 🇧🇳", "359": "Bulgaria 🇧🇬", "226": "Burkina Faso 🇧🇫", "257": "Burundi 🇧🇮",
        "238": "Cabo Verde 🇨🇻", "855": "Cambodia 🇰🇭", "237": "Cameroon 🇨🇲", "1": "Canada 🇨🇦", "236": "Central African Republic 🇨🇫", "235": "Chad 🇹🇩", "56": "Chile 🇨🇱", "86": "China 🇨🇳", "57": "Colombia 🇨🇴", "269": "Comoros 🇰🇲", "242": "Congo (Brazzaville) 🇨🇬", "243": "Congo (Kinshasa) 🇨🇩", "506": "Costa Rica 🇨🇷", "385": "Croatia 🇭🇷", "53": "Cuba 🇨🇺", "357": "Cyprus 🇨🇾", "420": "Czech Republic 🇨🇿",
        "45": "Denmark 🇩🇰", "253": "Djibouti 🇩🇯", "1767": "Dominica 🇩🇲", "1809": "Dominican Republic 🇩🇴", "593": "Ecuador 🇪🇨", "20": "Egypt 🇪🇬", "503": "El Salvador 🇸🇻", "240": "Equatorial Guinea 🇬🇶", "291": "Eritrea 🇪🇷", "372": "Estonia 🇪🇪", "268": "Eswatini 🇸🇿", "251": "Ethiopia 🇪🇹",
        "679": "Fiji 🇫🇯", "358": "Finland 🇫🇮", "33": "France 🇫🇷", "241": "Gabon 🇬🇦", "220": "Gambia 🇬🇲", "995": "Georgia 🇬🇪", "49": "Germany 🇩🇪", "233": "Ghana 🇬🇭", "30": "Greece 🇬🇷", "1473": "Grenada 🇬🇩", "502": "Guatemala 🇬🇹", "224": "Guinea 🇬🇳", "245": "Guinea-Bissau 🇬🇼", "592": "Guyana 🇬🇾",
        "509": "Haiti 🇭🇹", "504": "Honduras 🇭🇳", "36": "Hungary 🇭🇺", "354": "Iceland 🇮🇸", "91": "India 🇮🇳", "62": "Indonesia 🇮🇩", "98": "Iran 🇮🇷", "964": "Iraq 🇮🇶", "353": "Ireland 🇮🇪", "972": "Israel 🇮🇱", "39": "Italy 🇮🇹", "225": "Ivory Coast 🇨🇮",
        "1876": "Jamaica 🇯🇲", "81": "Japan 🇯🇵", "962": "Jordan 🇯🇴", "7": "Kazakhstan 🇰🇿", "254": "Kenya 🇰🇪", "686": "Kiribati 🇰🇮", "965": "Kuwait 🇰🇼", "996": "Kyrgyzstan 🇰🇬", "856": "Laos 🇱🇦", "371": "Latvia 🇱🇻", "961": "Lebanon 🇱🇧", "266": "Lesotho 🇱🇸", "231": "Liberia 🇱🇷", "218": "Libya 🇱🇾", "423": "Liechtenstein 🇱🇮", "370": "Lithuania 🇱🇹", "352": "Luxembourg 🇱🇺",
        "261": "Madagascar 🇲🇬", "265": "Malawi 🇲🇼", "60": "Malaysia 🇲🇾", "960": "Maldives 🇲🇻", "223": "Mali 🇲🇱", "356": "Malta 🇲🇹", "692": "Marshall Islands 🇲🇭", "222": "Mauritania 🇲🇷", "230": "Mauritius 🇲🇺", "52": "Mexico 🇲🇽", "691": "Micronesia 🇫🇲", "373": "Moldova 🇲🇩", "377": "Monaco 🇲🇨", "976": "Mongolia 🇲🇳", "382": "Montenegro 🇲🇪", "212": "Morocco 🇲🇦", "258": "Mozambique 🇲🇿", "95": "Myanmar 🇲🇲",
        "264": "Namibia 🇳🇦", "674": "Nauru 🇳🇷", "977": "Nepal 🇳🇵", "31": "Netherlands 🇳🇱", "64": "New Zealand 🇳🇿", "505": "Nicaragua 🇳🇮", "227": "Niger 🇳🇪", "234": "Nigeria 🇳🇬", "850": "North Korea 🇰🇵", "389": "North Macedonia 🇲🇰", "47": "Norway 🇳🇴",
        "968": "Oman 🇴🇲", "92": "Pakistan 🇵🇰", "680": "Palau 🇵🇼", "970": "Palestine 🇵🇸", "507": "Panama 🇵🇦", "675": "Papua New Guinea 🇵🇬", "595": "Paraguay 🇵🇾", "51": "Peru 🇵🇪", "63": "Philippines 🇵🇭", "48": "Poland 🇵🇱", "351": "Portugal 🇵🇹", "974": "Qatar 🇶🇦",
        "40": "Romania 🇷🇴", "7": "Russia 🇷🇺", "250": "Rwanda 🇷🇼", "1869": "Saint Kitts and Nevis 🇰🇳", "1758": "Saint Lucia 🇱🇨", "1784": "Saint Vincent and the Grenadines 🇻🇨", "685": "Samoa 🇼🇸", "378": "San Marino 🇸🇲", "239": "Sao Tome and Principe 🇸🇹", "966": "Saudi Arabia 🇸🇦", "221": "Senegal 🇸🇳", "381": "Serbia 🇷🇸", "248": "Seychelles 🇸🇨", "232": "Sierra Leone 🇸🇱", "65": "Singapore 🇸🇬", "421": "Slovakia 🇸🇰", "386": "Slovenia 🇸🇮", "677": "Solomon Islands 🇸🇧", "252": "Somalia 🇸🇴", "27": "South Africa 🇿🇦", "82": "South Korea 🇰🇷", "211": "South Sudan 🇸🇸", "34": "Spain 🇪🇸", "94": "Sri Lanka 🇱🇰", "249": "Sudan 🇸🇩", "597": "Suriname 🇸🇷", "46": "Sweden 🇸🇪", "41": "Switzerland 🇨🇭", "963": "Syria 🇸🇾",
        "886": "Taiwan 🇹🇼", "992": "Tajikistan 🇹🇯", "255": "Tanzania 🇹🇿", "66": "Thailand 🇹🇭", "670": "Timor-Leste 🇹🇱", "228": "Togo 🇹🇬", "676": "Tonga 🇹🇴", "1868": "Trinidad and Tobago 🇹🇹", "216": "Tunisia 🇹🇳", "90": "Turkey 🇹🇷", "993": "Turkmenistan 🇹🇲", "688": "Tuvalu 🇹🇻",
        "256": "Uganda 🇺🇬", "380": "Ukraine 🇺🇦", "971": "United Arab Emirates 🇦🇪", "44": "United Kingdom 🇬🇧", "1": "United States 🇺🇸", "598": "Uruguay 🇺🇾", "998": "Uzbekistan 🇺🇿",
        "678": "Vanuatu 🇻🇺", "379": "Vatican City 🇻🇦", "58": "Venezuela 🇻🇪", "84": "Vietnam 🇻🇳", "967": "Yemen 🇾🇪",
        "260": "Zambia 🇿🇲", "263": "Zimbabwe 🇿🇼"
    }
    clean_num = re.sub(r'\D', '', number)
    sorted_codes = sorted(countries_map.keys(), key=len, reverse=True)
    for code in sorted_codes:
        if clean_num.startswith(code): return countries_map[code], "English"
    return "Unknown 🌐", "English"

def detect_service(msg):
    msg = msg.upper()
    if any(k in msg for k in ["FACEBOOK", "FB"]): return "Facebook"
    if any(k in msg for k in ["INSTAGRAM", "IG", "INSTA"]): return "Instagram"
    if any(k in msg for k in ["WHATSAPP", "WA"]): return "WhatsApp"
    return "OTP"

def extract_otp(message_text):
    clean = message_text.replace(" ", "")
    match = re.search(r'\d{5,8}', clean)
    if match: return match.group()
    digits = "".join(filter(str.isdigit, message_text))
    return digits[:8] if len(digits) >= 5 else "00000"

def send_to_telegram(bot_instance, otp_full, display_number, actual_copy_number, otp_code):
    country_info, lang = get_country_info(actual_copy_number)
    service = detect_service(otp_full)
    current_time = time.strftime("%H:%M")
    text = (f"<blockquote>{country_info} • 📱 {service} •</blockquote>\n"
            f"☎️ {display_number}\n\n"
            f"<blockquote>⏰ {current_time} 🗣 {lang}</blockquote>")
    markup = types.InlineKeyboardMarkup()
    markup.row(types.InlineKeyboardButton(text=f"📋 {otp_code}", copy_text=types.CopyTextButton(text=otp_code)))
    markup.row(types.InlineKeyboardButton(text="▰ RANGE COPY ▰", copy_text=types.CopyTextButton(text=actual_copy_number)))
    markup.row(types.InlineKeyboardButton("✦ NUMBER BOT ✦", url=PANEL_BOT_URL), 
               types.InlineKeyboardButton("✦ METHOD ✦", url=RANGE_CHANNEL_URL))
    msg = bot_instance.send_message(CHANNEL_ID, text, reply_markup=markup, parse_mode="HTML")
    threading.Thread(target=lambda: (time.sleep(90), bot_instance.delete_message(CHANNEL_ID, msg.message_id)), daemon=True).start()

def run_bot1():
    url = "https://api.2oo9.cloud/MXS47FLFX0U/tness/@public/api/success-otp"
    while True:
        try:
            res = requests.get(url, headers={"mauthapi": API_KEY}, timeout=10).json()
            if res.get("meta", {}).get("code") == 200:
                history = pickle.load(open(DB_FILE, "rb")) if os.path.exists(DB_FILE) else {}
                for item in res.get("data", {}).get("otps", []):
                    oid = str(item.get("otp_id", ""))
                    if oid not in history:
                        num = str(item.get("number", ""))
                        masked = f"{num[:4]}★★{num[-4:]}" if len(num) >= 8 else num
                        code = extract_otp(item.get("message", ""))
                        send_to_telegram(bot1, item.get("message", ""), masked, num, code)
                        history[oid] = True
                        pickle.dump(history, open(DB_FILE, "wb"))
        except: pass
        time.sleep(10)

def run_bot2():
    url = "https://api.2oo9.cloud/MXS47FLFX0U/tness/@public/api/console"
    while True:
        try:
            res = requests.get(url, headers={"mauthapi": API_KEY}, timeout=10).json()
            if res.get("meta", {}).get("status") == "ok":
                history = pickle.load(open(DB_FILE, "rb")) if os.path.exists(DB_FILE) else {}
                for hit in res.get("data", {}).get("hits", []):
                    time_id = str(hit.get("time", ""))
                    if time_id not in history:
                        raw = str(hit.get("range", ""))
                        clean = re.sub(r'[Xx]', '', raw)
                        generated = f"{clean}{''.join([str(random.randint(0,9)) for _ in range(4)])}"
                        code = extract_otp(hit.get("message", ""))
                        send_to_telegram(bot2, hit.get("message", ""), generated, generated, code)
                        history[time_id] = True
                        pickle.dump(history, open(DB_FILE, "wb"))
        except: pass
        time.sleep(10)

if __name__ == "__main__":
    threading.Thread(target=run_bot1, daemon=True).start()
    threading.Thread(target=run_bot2, daemon=True).start()
    app = Flask(__name__)
    @app.route('/')
    def home(): return "All bots are running!"
    app.run(host="0.0.0.0", port=8080)
