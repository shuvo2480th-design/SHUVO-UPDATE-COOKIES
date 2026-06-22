import requests
import time
import telebot
import pickle
import os
import re
import random
import threading
import phonenumbers
from phonenumbers import geocoder
from telebot import types

# ---------------- CONFIG ----------------
BOT_TOKEN = "YOUR_NEW_TOKEN_HERE"  # নতুন টোকেনটি এখানে বসান
CHANNEL_ID = "-1002670575248"
API_KEY = "MUBTR1MKUBO"
API_URL = "https://api.2oo9.cloud/MXS47FLFX0U/tness/@public/api/console"
RANGE_CHANNEL_URL = "https://t.me/range_channele"
PANEL_BOT_URL = "https://t.me/shuvo_number_bot"

bot = telebot.TeleBot(BOT_TOKEN)
# সার্ভারে কনফ্লিক্ট এড়াতে এটি সবচেয়ে জরুরি
bot.remove_webhook() 

DB_FILE = "otp_history.pkl"

def get_country_info(number):
    try:
        clean_number = re.sub(r'\D', '', str(number))
        parsed_number = phonenumbers.parse("+" + clean_number, None)
        country_name = geocoder.country_name_for_number(parsed_number, "en")
        
        flags = {
            "Bangladesh": "🇧🇩", "Guinea": "🇬🇳", "United States": "🇺🇸", 
            "India": "🇮🇳", "United Kingdom": "🇬🇧", "Pakistan": "🇵🇰",
            "Nigeria": "🇳🇬", "Indonesia": "🇮🇩", "Saudi Arabia": "🇸🇦",
            "Russia": "🇷🇺", "China": "🇨🇳", "Germany": "🇩🇪", "Brazil": "🇧🇷",
            "Armenia": "🇦🇲", "Benin": "🇧🇯", "Central African Republic": "🇨🇫",
            "Ivory Coast": "🇨🇮", "Tanzania": "🇹🇿", "Lesotho": "🇱🇸", 
            "Kazakhstan": "🇰🇿", "Tajikistan": "🇹🇯"
        }
        
        flag = flags.get(country_name, "🌐")
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
    otp_full = hit.get("message", "")
    full_number = str(hit.get("range", ""))
    
    flag, country, lang = get_country_info(full_number)
    
    range_clean = re.sub(r'[Xx]', '', full_number)
    random_digits = ''.join([str(random.randint(0, 9)) for _ in range(4)])
    masked_number = f"{full_number[:4]}★★{random_digits}"
    
    otp_match = re.search(r'\b\d{5,8}\b', otp_full)
    otp_code = otp_match.group() if otp_match else ''.join(filter(str.isdigit, otp_full))[:8]
    
    service = detect_service(otp_full)
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
    markup.row(types.InlineKeyboardButton("✦ NUMBER BOT ✦", url=PANEL_BOT_URL), 
               types.InlineKeyboardButton("✦ METHOD ✦", url=RANGE_CHANNEL_URL))

    msg = bot.send_message(CHANNEL_ID, text, reply_markup=markup)
    threading.Thread(target=lambda: (time.sleep(90), bot.delete_message(CHANNEL_ID, msg.message_id))).start()

print("🚀 Bot is running perfectly...")
while True:
    try:
        res = requests.get(API_URL, headers={"mauthapi": API_KEY}, timeout=10).json()
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
        print(f"Error: {e}")
    time.sleep(10)
