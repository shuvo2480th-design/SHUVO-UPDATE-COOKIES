# -*- coding: utf-8 -*-

import requests
import time
import telebot
import re
import random
import threading
import json
import os
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
    return "Channel Bot is Running!"

def run_flask():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run_flask, daemon=True)
    t.start()

# ===================== CONFIG =====================
# বট ১ — আগের বট
BOT_TOKEN_1  = "8764978166:AAH5tQLO71RCoCN1qtAr6xebGxFYiRT9z4A"
# বট ২ — নতুন বট
BOT_TOKEN_2  = "8658807204:AAH6FSK5X0_haGRCQ_d-Vq4Gh1wLD0EsRgs"

CHANNEL_ID       = "-1002670575248"
API_KEY          = "MUBTR1MKUBO"
SUCCESS_OTP_URL  = "https://api.2oo9.cloud/MXS47FLFX0U/tness/@public/api/success-otp"
RANGE_CHANNEL_URL = "https://t.me/range_channele"
PANEL_BOT_URL    = "https://t.me/shuvo_number_bot"
HEADERS          = {"mauthapi": API_KEY}

# ২টা bot object
bot1 = telebot.TeleBot(BOT_TOKEN_1)
bot2 = telebot.TeleBot(BOT_TOKEN_2)

# ===================== পাঠানো OTP ট্র্যাক (memory) =====================
sent_otp_ids = set()

# ===================== দেশের পতাকা =====================
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

def get_country_from_number(number):
    """ফোন নম্বর থেকে দেশের নাম বের করো"""
    try:
        clean = re.sub(r'\D', '', str(number))
        parsed = phonenumbers.parse("+" + clean, None)
        country_name = geocoder.country_name_for_number(parsed, "en")
        return country_name if country_name else "Unknown"
    except Exception:
        return "Unknown"

def detect_service(msg):
    msg_upper = msg.upper()
    if any(k in msg_upper for k in ["FACEBOOK", "FB"]):
        return "Facebook"
    if any(k in msg_upper for k in ["INSTAGRAM", "IG", "INSTA"]):
        return "Instagram"
    if any(k in msg_upper for k in ["WHATSAPP", "WA"]):
        return "WhatsApp"
    if "TELEGRAM" in msg_upper:
        return "Telegram"
    return "OTP"

def extract_otp(message_text, phone_number=None):
    """Message থেকে সঠিক OTP বের করে — space দেওয়া OTP ও ধরে"""
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

def send_to_channel(bot_obj, item):
    """Channel এ OTP message পাঠাও"""
    otp_msg     = item.get("message", "")
    full_number = str(item.get("number", ""))
    msg_id      = item.get("id", "")

    # দেশের নাম ও পতাকা
    country_name = item.get("country", "") or get_country_from_number(full_number)
    flag         = get_flag(country_name)

    # OTP extract
    otp_code = extract_otp(otp_msg, full_number)
    if not otp_code:
        otp_code = re.sub(r'\D', '', otp_msg)[-6:] or "------"

    # সার্ভিস ধরো
    service = detect_service(otp_msg)

    # নাম্বার mask করো
    clean_num = re.sub(r'\D', '', full_number)
    if len(clean_num) >= 8:
        masked = clean_num[:4] + "★★" + clean_num[-4:]
    else:
        masked = clean_num

    current_time = time.strftime("%H:%M")

    text = (
        f"┏━━━━━━━━━━━━━━━━━━┓\n"
        f"┃ ✦ {masked} ✦   ┃\n"
        f"┣━━━━━━━━━━━━━━━━━━┫\n"
        f"┃ {flag} {country_name} • {service} ┃\n"
        f"┣━━━━━━━━━━━━━━━━━━┫\n"
        f"┃ ⏰ {current_time} • English ┃\n"
        f"┗━━━━━━━━━━━━━━━━━━┛"
    )

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
        msg = bot_obj.send_message(CHANNEL_ID, text, reply_markup=markup)
        # ৯০ সেকেন্ড পরে ডিলিট
        threading.Thread(
            target=lambda: (time.sleep(90), bot_obj.delete_message(CHANNEL_ID, msg.message_id)),
            daemon=True
        ).start()
    except Exception as e:
        print(f"[Send Error] {e}")

# ===================== OTP POLLER =====================
def poll_success_otp(bot_obj, bot_name):
    """success-otp API poll করে নতুন OTP আসলে channel এ পাঠাবে"""
    print(f"✅ {bot_name} polling started...")
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
                        send_to_channel(bot_obj, item)
                        time.sleep(1.5)
        except Exception as e:
            print(f"[{bot_name} Poll Error] {e}")
        time.sleep(5)

# ===================== MAIN =====================
if __name__ == "__main__":
    keep_alive()

    # বট ১ — thread এ চলবে
    t1 = threading.Thread(
        target=poll_success_otp,
        args=(bot1, "BOT-1"),
        daemon=True
    )
    # বট ২ — thread এ চলবে
    t2 = threading.Thread(
        target=poll_success_otp,
        args=(bot2, "BOT-2"),
        daemon=True
    )

    t1.start()
    t2.start()

    print("🚀 Both bots running!")

    # main thread জীবিত রাখো
    while True:
        time.sleep(60)
