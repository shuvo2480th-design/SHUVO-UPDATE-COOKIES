# -*- coding: utf-8 -*-
import requests
import time
import telebot
import pickle
import os
import pycountry
import re
import threading 
from flask import Flask
from threading import Thread
from telebot import types

# --- [KEEP ALIVE SYSTEM] ---
app = Flask('')

@app.route('/')
def home():
    return "OTP Worker System is Online & Running 24/7!"

def run_web_server():
    # Render-এর জন্য পোর্ট ডাইনামিক করা হয়েছে
    port = int(os.environ.get("PORT", 8081)) 
    try:
        app.run(host='0.0.0.0', port=port)
    except: pass

def keep_alive():
    t = Thread(target=run_web_server)
    t.daemon = True # থ্রেডটি মেইন প্রোগ্রামের সাথে বন্ধ হবে না
    t.start()
# ---------------------------------------------------------

# ---------------- CONFIG ----------------
BOT_TOKEN = "8764978166:AAEhHy4R82VK9FmygIyPAQaNxtYVfbx-eXY"
CHANNEL_ID = "-1002670575248"
API_KEY = "M_SX44INH5S"
RANGE_CHANNEL_URL = "https://t.me/range_channele"
PANEL_BOT_URL = "https://t.me/shuvo_number_bot" 
API_BASE = "https://stexsms.com/mapi/v1/public"

bot = telebot.TeleBot(BOT_TOKEN)
DB_FILE = "otp_history.pkl"

def save_history(data):
    try:
        if len(data) > 800:
            keys = list(data.keys())
            for k in keys[:200]: del data[k]
        with open(DB_FILE, "wb") as f:
            pickle.dump(data, f)
    except: pass

def load_history():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "rb") as f:
                return pickle.load(f)
        except: return {}
    return {}

sent_history = load_history()

def delete_message_after_delay(chat_id, message_id, delay=90):
    time.sleep(delay)
    try:
        bot.delete_message(chat_id, message_id)
    except: pass

def detect_language(otp_full):
    otp_text = str(otp_full).lower()
    if any(word in otp_text for word in ['votre', 'code', 'est']):
        return "French"
    elif any(word in otp_text for word in ['su codigo', 'es']):
        return "Spanish"
    else:
        return "English"

def detect_service_tag(otp_full):
    otp_text = str(otp_full).upper()
    if any(x in otp_text for x in ["FACEBOOK", "FB"]): return "FB"
    elif any(x in otp_text for x in ["INSTAGRAM", "IG"]): return "IG"
    elif any(x in otp_text for x in ["WHATSAPP", "WA"]): return "WA"
    else: return "OTP"

def get_country_details(country_name):
    try:
        country = pycountry.countries.search_fuzzy(country_name)[0]
        flag = "".join(chr(127397 + ord(c)) for c in country.alpha_2)
        return flag, country.alpha_2.upper()
    except:
        return "🏳", "UN"

def extract_real_otp(otp_full):
    otp_full = str(otp_full)
    dash_match = re.search(r'\d{3}-\d{3}', otp_full)
    if dash_match: return dash_match.group()
    matches = re.findall(r'\b\d{4,8}\b', otp_full)
    if matches: return matches[0] 
    return ''.join(filter(str.isdigit, otp_full))[:8]

def send_styled_otp(number, flag, short_code, otp_code, service_tag, otp_full):
    current_time = time.strftime("%H:%M")
    lang = detect_language(otp_full)
    masked_number = f"{number[:4]}★★{number[-4:]}" if len(number) > 8 else number

    # আপনার দেওয়া ক্লিপ অনুযায়ী মেসেজ বডি
    text = (
        f"{flag} {short_code} • {service_tag} •\n"
        f"<code>{masked_number}</code> • <b>{lang}</b> <code>{current_time}</code>"
    )

    markup = types.InlineKeyboardMarkup()
    markup.row(types.InlineKeyboardButton(text=f"{otp_code}", copy_text=types.CopyTextButton(text=otp_code)))
    markup.row(
        types.InlineKeyboardButton("Number", url=PANEL_BOT_URL),
        types.InlineKeyboardButton("Range", url=RANGE_CHANNEL_URL)
    )

    try:
        sent_msg = bot.send_message(CHANNEL_ID, text, reply_markup=markup, parse_mode="HTML")
        threading.Thread(target=delete_message_after_delay, args=(CHANNEL_ID, sent_msg.message_id), daemon=True).start()
    except: pass

def main_otp_loop():
    print("🚀 OTP Worker is scanning for codes...")
    headers = {
        "mapikey": API_KEY,
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json"
    }
    
    # ইনফিনিটি লুপ যাতে বট কখনো না মরে
    while True:
        try:
            # টাইমআউট দেওয়া হয়েছে যাতে রিকোয়েস্ট হ্যাং না হয়ে থাকে
            res = requests.get(f"{API_BASE}/numsuccess/info", headers=headers, timeout=20).json()
            
            if res and res.get("meta", {}).get("status") == "success":
                otps = res.get("data", {}).get("otps", [])
                
                if isinstance(otps, list):
                    for otp_entry in otps:
                        number = str(otp_entry.get("number", ""))
                        otp_full = str(otp_entry.get("otp", "")).strip()
                        
                        if not number or not otp_full: continue
                        
                        otp_code = extract_real_otp(otp_full)
                        service_tag = detect_service_tag(otp_full)
                        
                        # ডুপ্লিকেট চেক
                        if number in sent_history and otp_code in sent_history[number]: 
                            continue
                        
                        if number not in sent_history: 
                            sent_history[number] = []
                        
                        sent_history[number].append(otp_code)
                        save_history(sent_history)
                        
                        flag, short_code = get_country_details(otp_entry.get("country", "Unknown"))
                        send_styled_otp(number, flag, short_code, otp_code, service_tag, otp_full)
            
            # ৫ সেকেন্ড বিরতি
            time.sleep(5)
                            
        except Exception as e: 
            # কোনো এরর হলে বট বন্ধ হবে না, ১০ সেকেন্ড অপেক্ষা করে আবার নিজে নিজে চলবে
            print(f"⚠️ Auto-Restarting Worker due to: {e}")
            time.sleep(10)
            continue

if __name__ == "__main__":
    # কিপ এলাইভ চালু করা
    keep_alive()
    
    # মেইন লুপ অটো-রিস্টার্ট প্রোটেকশন সহ
    while True:
        try:
            main_otp_loop()
        except:
            time.sleep(5)
