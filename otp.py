# -*- coding: utf-8 -*-

import requests
import time
import telebot
import pickle
import os
import re
import random
import threading
import pycountry
import phonenumbers
from phonenumbers import geocoder
from telebot import types
from flask import Flask
from threading import Thread

# ===================== FLASK KEEP-ALIVE (Render এর জন্য) =====================
app = Flask('')

@app.route('/')
def home():
    return "Bot is Running!"

def run_flask():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run_flask, daemon=True)
    t.start()

# ===================== CONFIG =====================
# বট ১ — console API
BOT_TOKEN_1 = "8764978166:AAH5tQLO71RCoCN1qtAr6xebGxFYiRT9z4A"
# বট ২ — success-otp API
BOT_TOKEN_2 = "8658807204:AAH6FSK5X0_haGRCQ_d-Vq4Gh1wLD0EsRgs"

CHANNEL_ID        = "-1002670575248"
API_KEY           = "MUBTR1MKUBO"
CONSOLE_URL       = "https://api.2oo9.cloud/MXS47FLFX0U/tness/@public/api/console"
SUCCESS_OTP_URL   = "https://api.2oo9.cloud/MXS47FLFX0U/tness/@public/api/success-otp"
RANGE_CHANNEL_URL = "https://t.me/range_channele"
PANEL_BOT_URL     = "https://t.me/shuvo_number_bot"
HEADERS           = {"mauthapi": API_KEY}
DB_FILE           = "otp_history.pkl"

bot1 = telebot.TeleBot(BOT_TOKEN_1)
bot2 = telebot.TeleBot(BOT_TOKEN_2)
bot1.remove_webhook()
bot2.remove_webhook()

# বট ২ এর পাঠানো OTP track (memory)
sent_otp_ids = set()

# ===================== পতাকা (auto — সব দেশ) =====================
COUNTRY_NAME_MAP = {
    "ivory coast":    "CI",
    "ivory coast 2":  "CI",
    "côte d'ivoire":  "CI",
    "cote d'ivoire":  "CI",
    "cote divoire":   "CI",
    "guinea bissau":  "GW",
    "guinea-bissau":  "GW",
    "south korea":    "KR",
    "north korea":    "KP",
    "russia":         "RU",
    "tanzania":       "TZ",
    "syria":          "SY",
    "iran":           "IR",
    "vietnam":        "VN",
    "laos":           "LA",
    "moldova":        "MD",
    "congo":          "CG",
    "dr congo":       "CD",
    "palestine":      "PS",
    "taiwan":         "TW",
    "cape verde":     "CV",
    "myanmar":        "MM",
    "eswatini":       "SZ",
    "swaziland":      "SZ",
    "east timor":     "TL",
    "micronesia":     "FM",
    "curacao":        "CW",
    "kosovo":         "XK",
    "lesotho":        "LS",
    "benin":          "BJ",
    "armenia":        "AM",
    "kazakhstan":     "KZ",
    "tajikistan":     "TJ",
    "central african republic": "CF",
}

def get_flag(country_name):
    if not country_name:
        return "🌐"
    name_lower = country_name.lower().strip()
    if name_lower in COUNTRY_NAME_MAP:
        alpha2 = COUNTRY_NAME_MAP[name_lower]
        return "".join(chr(ord(x) + 127397) for x in alpha2.upper())
    try:
        c = pycountry.countries.lookup(country_name)
        return "".join(chr(ord(x) + 127397) for x in c.alpha_2.upper())
    except Exception:
        pass
    try:
        results = pycountry.countries.search_fuzzy(country_name)
        if results:
            return "".join(chr(ord(x) + 127397) for x in results[0].alpha_2.upper())
    except Exception:
        pass
    return "🌐"

# ===================== বট ১ এর ফাংশন (console API — হুবহু আগের মতো) =====================
def get_country_info(number):
    try:
        clean_number = re.sub(r'\D', '', str(number))
        parsed_number = phonenumbers.parse("+" + clean_number, None)
        country_name = geocoder.country_name_for_number(parsed_number, "en")
        flag = get_flag(country_name)
        return flag, country_name if country_name else "Unknown", "English"
    except:
        return "🌐", "Unknown", "English"

def detect_service(msg):
    msg = msg.upper()
    if any(k in msg for k in ["FACEBOOK", "FB"]): return "Facebook"
    if any(k in msg for k in ["INSTAGRAM", "IG", "INSTA"]): return "Instagram"
    if any(k in msg for k in ["WHATSAPP", "WA"]): return "WhatsApp"
    return "OTP"

def send_styled_otp(hit):
    otp_full    = hit.get("message", "")
    full_number = str(hit.get("range", ""))

    flag, country, lang = get_country_info(full_number)

    range_clean    = re.sub(r'[Xx]', '', full_number)
    random_digits  = ''.join([str(random.randint(0, 9)) for _ in range(4)])
    masked_number  = f"{full_number[:4]}★★{random_digits}"

    otp_match = re.search(r'\b\d{5,8}\b', otp_full)
    otp_code  = otp_match.group() if otp_match else ''.join(filter(str.isdigit, otp_full))[:8]

    service      = detect_service(otp_full)
    current_time = time.strftime("%H:%M")

    text = (f"┏━━━━━━━━━━━━━━━━━━┓\n"
            f"┃ ✦ {masked_number} ✦   ┃\n"
            f"┣━━━━━━━━━━━━━━━━━━┫\n"
            f"┃ {flag} {country} • {service} ┃\n"
            f"┣━━━━━━━━━━━━━━━━━━┫\n"
            f"┃ ⏰ {current_time} • {lang} ┃\n"
            f"┗━━━━━━━━━━━━━━━━━━┛")

    markup = types.InlineKeyboardMarkup()
    markup.row(types.InlineKeyboardButton(text=f"📋 {otp_code}", copy_text=types.CopyTextButton(text=otp_code)))
    markup.row(types.InlineKeyboardButton(text="▰ RANGE COPY ▰", copy_text=types.CopyTextButton(text=range_clean)))
    markup.row(
        types.InlineKeyboardButton("✦ NUMBER BOT ✦", url=PANEL_BOT_URL),
        types.InlineKeyboardButton("✦ METHOD ✦", url=RANGE_CHANNEL_URL)
    )

    msg = bot1.send_message(CHANNEL_ID, text, reply_markup=markup, parse_mode="HTML")
    threading.Thread(
        target=lambda: (time.sleep(90), bot1.delete_message(CHANNEL_ID, msg.message_id)),
        daemon=True
    ).start()

# বট ১ loop
def run_bot1():
    print("🚀 BOT-1 (console) started...")
    while True:
        try:
            res = requests.get(CONSOLE_URL, headers=HEADERS, timeout=10).json()
            if res.get("meta", {}).get("status") == "ok":
                history = pickle.load(open(DB_FILE, "rb")) if os.path.exists(DB_FILE) else {}
                for hit in res.get("data", {}).get("hits", []):
                    msg_time = str(hit.get("time", ""))
                    if msg_time not in history:
                        send_styled_otp(hit)
                        history[msg_time] = True
                        pickle.dump(history, open(DB_FILE, "wb"))
                        time.sleep(1.5)
        except Exception as e:
            print(f"[BOT-1 Error] {e}")
        time.sleep(10)

# ===================== বট ২ এর ফাংশন (success-otp API) =====================
def extract_otp(message_text, phone_number=None):
    if not message_text:
        return None
    phone_digits = re.sub(r'\D', '', str(phone_number)) if phone_number else ""

    # spaced OTP যেমন "138 740"
    spaced_matches = re.findall(r'\b(\d[\d ]{2,12}\d)\b', message_text)
    for match in spaced_matches:
        joined = match.replace(" ", "")
        if not joined.isdigit():
            continue
        if phone_digits and (joined in phone_digits or phone_digits in joined):
            continue
        if 4 <= len(joined) <= 10:
            return joined

    # সাধারণ ৪-১০ digit
    candidates = re.findall(r'\b(\d{4,10})\b', message_text)
    for candidate in candidates:
        if phone_digits:
            if candidate in phone_digits:
                continue
            if phone_digits in candidate:
                continue
            if phone_digits[-10:] in candidate:
                continue
        if 4 <= len(candidate) <= 10:
            return candidate

    # fallback
    all_digits = re.sub(r'\D', '', message_text)
    if phone_digits:
        all_digits = all_digits.replace(phone_digits, "")
    if len(all_digits) >= 4:
        return all_digits[-6:] if len(all_digits) >= 6 else all_digits
    return None

def get_country_from_number(number):
    try:
        clean = re.sub(r'\D', '', str(number))
        parsed = phonenumbers.parse("+" + clean, None)
        country_name = geocoder.country_name_for_number(parsed, "en")
        return country_name if country_name else "Unknown"
    except Exception:
        return "Unknown"

def send_to_channel_bot2(item):
    otp_msg     = item.get("message", "")
    # success-otp API তে "number" field এ full number থাকে
    full_number = str(item.get("number", ""))
    clean_num   = re.sub(r'\D', '', full_number)

    # দেশ ও পতাকা — number থেকে auto
    country_name = get_country_from_number(full_number)
    flag         = get_flag(country_name)

    # সঠিক OTP extract
    otp_code = extract_otp(otp_msg, full_number)
    if not otp_code:
        otp_code = re.sub(r'\D', '', otp_msg)[-6:] or "------"

    service = detect_service(otp_msg)

    # নাম্বার mask
    if len(clean_num) >= 8:
        masked = clean_num[:4] + "★★" + clean_num[-4:]
    else:
        masked = clean_num

    current_time = time.strftime("%H:%M")

    text = (f"┏━━━━━━━━━━━━━━━━━━┓\n"
            f"┃ ✦ {masked} ✦   ┃\n"
            f"┣━━━━━━━━━━━━━━━━━━┫\n"
            f"┃ {flag} {country_name} • {service} ┃\n"
            f"┣━━━━━━━━━━━━━━━━━━┫\n"
            f"┃ ⏰ {current_time} • English ┃\n"
            f"┗━━━━━━━━━━━━━━━━━━┛")

    markup = types.InlineKeyboardMarkup()
    markup.row(types.InlineKeyboardButton(
        text=f"📋 {otp_code}",
        copy_text=types.CopyTextButton(text=otp_code)
    ))
    markup.row(types.InlineKeyboardButton(
        text="▰ RANGE COPY ▰",
        copy_text=types.CopyTextButton(text=clean_num)
    ))
    markup.row(
        types.InlineKeyboardButton("✦ NUMBER BOT ✦", url=PANEL_BOT_URL),
        types.InlineKeyboardButton("✦ METHOD ✦",     url=RANGE_CHANNEL_URL)
    )

    try:
        msg = bot2.send_message(CHANNEL_ID, text, reply_markup=markup)
        threading.Thread(
            target=lambda: (time.sleep(90), bot2.delete_message(CHANNEL_ID, msg.message_id)),
            daemon=True
        ).start()
    except Exception as e:
        print(f"[BOT-2 Send Error] {e}")

# বট ২ loop — success-otp API (bot.py এর auto_check_otp এর মতো)
def run_bot2():
    print("🚀 BOT-2 (success-otp) started...")
    while True:
        try:
            r    = requests.get(SUCCESS_OTP_URL, headers=HEADERS, timeout=10)
            data = r.json()
            if data.get("meta", {}).get("code") == 200:
                otps = data.get("data", {}).get("otps", [])
                for item in otps:
                    msg_id = str(item.get("id", ""))
                    if msg_id and msg_id not in sent_otp_ids:
                        sent_otp_ids.add(msg_id)
                        send_to_channel_bot2(item)
                        time.sleep(1.5)
        except Exception as e:
            print(f"[BOT-2 Error] {e}")
        time.sleep(2)

# ===================== MAIN =====================
if __name__ == "__main__":
    keep_alive()

    threading.Thread(target=run_bot1, daemon=True).start()
    threading.Thread(target=run_bot2, daemon=True).start()

    print("✅ Both bots running!")

    while True:
        time.sleep(60)
