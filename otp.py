import requests
import time
import telebot
import pickle
import os
import re
import threading
import random
import phonenumbers
from phonenumbers import geocoder
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

# অটো কান্ট্রি ডিটেকশন ফাংশন
def get_country_info(number):
    try:
        formatted_number = "+" + number if not number.startswith("+") else number
        parsed_number = phonenumbers.parse(formatted_number, None)
        country_name = geocoder.description_for_number(parsed_number, "en")
        region_code = phonenumbers.region_code_for_number(parsed_number)
        flag = "".join([chr(127462 + ord(char) - ord('A')) for char in region_code.upper()])
        return flag, country_name, "English"
    except:
        return "🌐", "Unknown", "English"

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
    flag, country, lang = get_country_info(actual_copy_number)
    service = detect_service(otp_full)
    current_time = time.strftime("%H:%M")

    text = (f"<blockquote>{flag} {country} • 📱 {service} •</blockquote>\n"
            f"☎️ {display_number}\n\n"
            f"<blockquote>⏰ {current_time} 🗣 {lang}</blockquote>")

    markup = types.InlineKeyboardMarkup()
    markup.row(types.InlineKeyboardButton(text=f"📋 {otp_code}", copy_text=types.CopyTextButton(text=otp_code)))
    markup.row(types.InlineKeyboardButton(text="▰ RANGE COPY ▰", copy_text=types.CopyTextButton(text=actual_copy_number)))
    markup.row(types.InlineKeyboardButton("✦ NUMBER BOT ✦", url=PANEL_BOT_URL), 
               types.InlineKeyboardButton("✦ METHOD ✦", url=RANGE_CHANNEL_URL))
    
    msg = bot_instance.send_message(CHANNEL_ID, text, reply_markup=markup, parse_mode="HTML")
    threading.Thread(target=lambda: (time.sleep(90), bot_instance.delete_message(CHANNEL_ID, msg.message_id)), daemon=True).start()

# --- BOT 1 LOGIC (Success OTP Duplicate Check) ---
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

# --- BOT 2 LOGIC (Range Console with 4-digit randomization) ---
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
                        # ৪ ডিজিট কেটে নতুন রেন্জ জেনারেট
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
