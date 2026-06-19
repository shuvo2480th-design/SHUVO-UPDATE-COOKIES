import requests
import time
import telebot
import pickle
import os
import re
import threading
import random
from telebot import types

# ---------------- CONFIG ----------------
BOT_TOKEN = "8658807204:AAHuvlFfHgb19m1wKHkJbeyYcf-50SuaMi8"
CHANNEL_ID = "-1002670575248"
API_KEY = "MUBTR1MKUBO"
API_URL = "https://api.2oo9.cloud/MXS47FLFX0U/tness/@public/api/success-otp"
RANGE_CHANNEL_URL = "https://t.me/range_channele"
PANEL_BOT_URL = "https://t.me/shuvo_number_bot"

bot = telebot.TeleBot(BOT_TOKEN)
DB_FILE = "otp_history.pkl"

def get_country_info(number):
    if number.startswith("224"): 
        return "🇬🇳", "Guinea", "English"
    elif number.startswith("880"):
        return "🇧🇩", "Bangladesh", "Bengali"
    return "🇬🇳", "Guinea", "English"

def detect_service(msg):
    msg = msg.upper()
    if any(k in msg for k in ["FACEBOOK", "FB"]): return "Facebook"
    if any(k in msg for k in ["INSTAGRAM", "IG", "INSTA"]): return "Instagram"
    if any(k in msg for k in ["WHATSAPP", "WA"]): return "WhatsApp"
    return "OTP"

def send_styled_otp(otp_item):
    otp_full = otp_item.get("message", "")
    full_number = str(otp_item.get("number", ""))
    
    flag, country, lang = get_country_info(full_number)
    
    # সঠিক মাস্কিং (শুরুতে ৪টি, শেষে ৪টি ডিজিট)
    masked_number = f"{full_number[:4]}★★{full_number[-4:]}" if len(full_number) >= 8 else full_number
    
    # ওটিপি কোড এক্সট্রাকশন (৫-৮ ডিজিট, N/A হবে না)
    clean_msg = otp_full.replace(" ", "")
    otp_match = re.search(r'\d{5,8}', clean_msg)
    otp_code = otp_match.group() if otp_match else "".join(filter(str.isdigit, otp_full))[:8]
    
    service = detect_service(otp_full)
    current_time = time.strftime("%H:%M")

    # ফরম্যাটিং
    text = (f"<blockquote>{flag} {country} • 📱 {service} •</blockquote>\n"
            f"☎️ {masked_number}\n\n"
            f"<blockquote>⏰ {current_time} 🗣 {lang}</blockquote>")

    markup = types.InlineKeyboardMarkup()
    markup.row(types.InlineKeyboardButton(text=f"📋 {otp_code}", copy_text=types.CopyTextButton(text=otp_code)))
    markup.row(types.InlineKeyboardButton(text="▰ RANGE COPY ▰", copy_text=types.CopyTextButton(text=full_number)))
    markup.row(types.InlineKeyboardButton("✦ NUMBER BOT ✦", url=PANEL_BOT_URL), 
               types.InlineKeyboardButton("✦ METHOD ✦", url=RANGE_CHANNEL_URL))

    msg = bot.send_message(CHANNEL_ID, text, reply_markup=markup, parse_mode="HTML")
    threading.Thread(target=lambda: (time.sleep(90), bot.delete_message(CHANNEL_ID, msg.message_id))).start()

print("🚀 Bot is running perfectly with all fixes...")

while True:
    try:
        res = requests.get(API_URL, headers={"mauthapi": API_KEY}, timeout=10).json()
        if res.get("meta", {}).get("code") == 200:
            history = pickle.load(open(DB_FILE, "rb")) if os.path.exists(DB_FILE) else {}
            for otp_item in res.get("data", {}).get("otps", []):
                otp_id = str(otp_item.get("otp_id", ""))
                if otp_id not in history:
                    send_styled_otp(otp_item)
                    history[otp_id] = True
                    pickle.dump(history, open(DB_FILE, "wb"))
                    time.sleep(1.5)
    except Exception as e:
        print(f"Error: {e}")
    time.sleep(10)
