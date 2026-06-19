import requests
import time
import telebot
import pickle
import os
import re
import threading
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
    if number.startswith("224"): return "🇬🇳", "Guinea", "English"
    elif number.startswith("880"): return "🇧🇩", "Bangladesh", "Bengali"
    return "🇬🇳", "Guinea", "English"

def detect_service(msg):
    msg = msg.upper()
    if any(k in msg for k in ["FACEBOOK", "FB"]): return "Facebook"
    if any(k in msg for k in ["INSTAGRAM", "IG", "INSTA"]): return "Instagram"
    if any(k in msg for k in ["WHATSAPP", "WA"]): return "WhatsApp"
    return "OTP"

def send_to_telegram(bot_instance, otp_full, full_number, otp_code):
    flag, country, lang = get_country_info(full_number)
    masked_number = f"{full_number[:4]}★★{full_number[-4:]}" if len(full_number) >= 8 else full_number
    service = detect_service(otp_full)
    current_time = time.strftime("%H:%M")

    text = (f"<blockquote>{flag} {country} • 📱 {service} •</blockquote>\n"
            f"☎️ {masked_number}\n\n"
            f"<blockquote>⏰ {current_time} 🗣 {lang}</blockquote>")

    markup = types.InlineKeyboardMarkup()
    markup.row(types.InlineKeyboardButton(text=f"📋 {otp_code}", copy_text=types.CopyTextButton(text=otp_code)))
    markup.row(types.InlineKeyboardButton(text="▰ RANGE COPY ▰", copy_text=types.CopyTextButton(text=full_number)))
    markup.row(types.InlineKeyboardButton("✦ NUMBER BOT ✦", url=PANEL_BOT_URL), 
               types.InlineKeyboardButton("✦ METHOD ✦", url=RANGE_CHANNEL_URL))
    
    # মেসেজ পাঠানো
    msg = bot_instance.send_message(CHANNEL_ID, text, reply_markup=markup, parse_mode="HTML")
    
    # ৯০ সেকেন্ড পর মেসেজ অটো ডিলিট করার থ্রেড
    threading.Thread(target=lambda: (time.sleep(90), bot_instance.delete_message(CHANNEL_ID, msg.message_id)), daemon=True).start()

# --- BOT 1 LOGIC ---
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
                        code = re.search(r'\d{5,8}', item.get("message", "").replace(" ", ""))
                        code = code.group() if code else "".join(filter(str.isdigit, item.get("message", "")))[:8]
                        send_to_telegram(bot1, item.get("message", ""), item.get("number", ""), code)
                        history[oid] = True
                        pickle.dump(history, open(DB_FILE, "wb"))
        except: pass
        time.sleep(10)

# --- BOT 2 LOGIC ---
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
                        code = re.search(r'\d{5,8}', hit.get("message", "").replace(" ", ""))
                        code = code.group() if code else "".join(filter(str.isdigit, hit.get("message", "")))[:8]
                        send_to_telegram(bot2, hit.get("message", ""), str(hit.get("range", "")), code)
                        history[time_id] = True
                        pickle.dump(history, open(DB_FILE, "wb"))
        except: pass
        time.sleep(10)

# --- START ---
if __name__ == "__main__":
    threading.Thread(target=run_bot1, daemon=True).start()
    threading.Thread(target=run_bot2, daemon=True).start()
    
    app = Flask(__name__)
    @app.route('/')
    def home(): return "All bots are running!"
    app.run(host="0.0.0.0", port=8080)
