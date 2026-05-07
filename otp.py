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
    return "OTP Worker System is Online!"

def run_web_server():
    # পোর্ট ৮০৮১ রাখা হয়েছে যাতে bot.py এর সাথে সংঘর্ষ না হয়
    app.run(host='0.0.0.0', port=8081)

def keep_alive():
    t = Thread(target=run_web_server)
    t.setDaemon(True)
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
    # হিস্ট্রি ফাইল খুব বেশি বড় হয়ে গেলে পুরানোগুলো ছেঁটে ফেলার লজিক (ঐচ্ছিক)
    if len(data) > 500:
        keys = list(data.keys())
        for k in keys[:100]: del data[k]
    with open(DB_FILE, "wb") as f:
        pickle.dump(data, f)

def load_history():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "rb") as f:
                return pickle.load(f)
        except: return {}
    return {}

sent_history = load_history()

# --- অটো ডিলিট ফাংশন (অবিকল রাখা হয়েছে) ---
def delete_message_after_delay(chat_id, message_id, delay=90):
    time.sleep(delay)
    try:
        bot.delete_message(chat_id, message_id)
        print(f"🗑️ Message {message_id} cleaned up.")
    except: pass

def detect_language(otp_full):
    otp_text = otp_full.lower()
    if any(word in otp_text for word in ['votre', 'code', 'est']):
        return "French"
    elif any(word in otp_text for word in ['su codigo', 'es']):
        return "Spanish"
    else:
        return "English"

def detect_service_tag(otp_full):
    otp_text = otp_full.upper()
    if any(x in otp_text for x in ["FACEBOOK", "FB"]): return "FB"
    elif any(x in otp_text for x in ["INSTAGRAM", "IG"]): return "IG"
    elif any(x in otp_text for x in ["WHATSAPP", "WA"]): return "WA"
    else: return "OTP"

def get_country_details(country_name):
    try:
        # সার্চ অপ্টিমাইজ করা হয়েছে
        country = pycountry.countries.get(name=country_name.title()) or pycountry.countries.search_fuzzy(country_name)[0]
        flag = "".join(chr(127397 + ord(c)) for c in country.alpha_2)
        return flag, country.alpha_2.upper()
    except:
        return "🏳", "UN"

def extract_real_otp(otp_full):
    dash_match = re.search(r'\d{3}-\d{3}', otp_full)
    if dash_match: return dash_match.group()
    matches = re.findall(r'\b\d{4,8}\b', otp_full)
    if matches: return matches[0] 
    return ''.join(filter(str.isdigit, otp_full))[:8]

def send_styled_otp(number, flag, short_code, otp_code, service_tag, otp_full):
    current_time = time.strftime("%H:%M")
    lang = detect_language(otp_full)
    
    # নাম্বার মাস্কিং লজিক
    masked_number = f"{number[:4]}★★{number[-4:]}" if len(number) > 8 else number

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
        # ব্যাকগ্রাউন্ড থ্রেডে ডিলিট ফাংশন রান করা
        threading.Thread(target=delete_message_after_delay, args=(CHANNEL_ID, sent_msg.message_id), daemon=True).start()
    except Exception as e:
        print(f"❌ Send Error: {e}")

# --- মেইন লুপ ---
def main_otp_loop():
    print("🚀 OTP Worker is scanning for codes...")
    # API রিকোয়েস্টের জন্য হেডার
    headers = {
        "mapikey": API_KEY,
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/110.0.0.0 Safari/537.36"
    }
    
    while True:
        try:
            res = requests.get(f"{API_BASE}/numsuccess/info", headers=headers, timeout=15).json()
            
            if res and res.get("meta", {}).get("status") == "success":
                otps = res.get("data", {}).get("otps", [])
                for otp_entry in otps:
                    number = str(otp_entry.get("number", ""))
                    otp_full = str(otp_entry.get("otp", "")).strip()
                    
                    otp_code = extract_real_otp(otp_full)
                    service_tag = detect_service_tag(otp_full)
                    
                    if not number or not otp_code: continue
                    
                    # ডুপ্লিকেট চেক
                    if number in sent_history and otp_code in sent_history[number]: continue
                    
                    if number not in sent_history: sent_history[number] = []
                    sent_history[number].append(otp_code)
                    save_history(sent_history)
                    
                    flag, short_code = get_country_details(otp_entry.get("country", "Unknown"))
                    send_styled_otp(number, flag, short_code, otp_code, service_tag, otp_full)
                    print(f"✅ New OTP Forwarded: {number}")
                            
        except Exception as e: 
            print(f"⚠️ Worker Warning: {e}")
            
        time.sleep(5) # API রেট লিমিট এড়াতে ৫ সেকেন্ড বিরতি

if __name__ == "__main__":
    keep_alive()
    main_otp_loop()
