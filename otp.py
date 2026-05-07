import requests
import time
import telebot
import pickle
import os
import pycountry
import re
import threading 
from telebot import types

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
    with open(DB_FILE, "wb") as f:
        pickle.dump(data, f)

def load_history():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "rb") as f:
            return pickle.load(f)
    return {}

sent_history = load_history()

# --- ১ মিনিট ৩০ সেকেন্ড (৯০ সেকেন্ড) পর ডিলিট করার ফাংশন ---
def delete_message_after_delay(chat_id, message_id, delay=90):
    time.sleep(delay)
    try:
        bot.delete_message(chat_id, message_id)
        print(f"🗑️ Message {message_id} auto-deleted after 1m 30s.")
    except Exception as e:
        print(f"❌ Could not delete: {e}")

def detect_language(otp_full):
    otp_text = otp_full.lower()
    if any(word in otp_text for word in ['votre', 'votre code', 'est']):
        return "French"
    elif any(word in otp_text for word in ['su codigo', 'es']):
        return "Spanish"
    else:
        return "English"

def detect_service_tag(otp_full):
    otp_text = otp_full.upper()
    if "FACEBOOK" in otp_text or "FB" in otp_text: return "FB"
    elif "INSTAGRAM" in otp_text or "IG" in otp_text: return "IG"
    elif "WHATSAPP" in otp_text or "WA" in otp_text: return "WA"
    else: return "OTP"

def get_country_details(country_name):
    try:
        country = pycountry.countries.get(name=country_name.title()) or pycountry.countries.search_fuzzy(country_name)[0]
        flag = "".join(chr(127397 + ord(c)) for c in country.alpha_2)
        return flag, country.alpha_2.upper()
    except:
        return "🏳", "UN"

def extract_real_otp(otp_full):
    dash_match = re.search(r'\d{3}-\d{3}', otp_full)
    if dash_match: return dash_match.group()
    matches = re.findall(r'\b\d{5,8}\b', otp_full)
    if matches: return matches[0] 
    return ''.join(filter(str.isdigit, otp_full))[:8]

def send_styled_otp(number, flag, short_code, otp_code, service_tag, otp_full):
    current_time = time.strftime("%H:%M")
    lang = detect_language(otp_full)
    
    if len(number) > 8:
        masked_number = f"{number[:4]}★★{number[-4:]}"
    else:
        masked_number = number

    text = (
        f"{flag} {short_code} • {service_tag} •\n"
        f"<code>{masked_number}</code> • <b>{lang}</b> <code>{current_time}</code>"
    )

    markup = types.InlineKeyboardMarkup()
    
    # বাটন থেকে সব ইমোজি রিমুভ করা হয়েছে
    otp_btn = types.InlineKeyboardButton(
        text=f"{otp_code}", 
        copy_text=types.CopyTextButton(text=otp_code)
    )
    
    number_btn = types.InlineKeyboardButton("Number", url=PANEL_BOT_URL)
    range_btn = types.InlineKeyboardButton("Range", url=RANGE_CHANNEL_URL)

    markup.row(otp_btn)
    markup.row(number_btn, range_btn)

    sent_msg = bot.send_message(CHANNEL_ID, text, reply_markup=markup, parse_mode="HTML")
    
    # ৯০ সেকেন্ড পর ডিলিট হওয়ার জন্য থ্রেড স্টার্ট
    threading.Thread(target=delete_message_after_delay, args=(CHANNEL_ID, sent_msg.message_id)).start()

print("🚀 Bot is Starting with 1m 30s Auto-Delete...")

while True:
    try:
        url = f"{API_BASE}/numsuccess/info"
        headers = {"mapikey": API_KEY}
        res = requests.get(url, headers=headers, timeout=10).json()
        
        if res and isinstance(res.get("data"), dict):
            otps = res["data"].get("otps", [])
            for otp_entry in otps:
                number = str(otp_entry.get("number", ""))
                otp_full = str(otp_entry.get("otp", "")).strip()
                
                otp_code = extract_real_otp(otp_full)
                service_tag = detect_service_tag(otp_full)
                
                if not number or not otp_code: continue
                if number in sent_history and otp_code in sent_history[number]: continue
                
                if number not in sent_history: sent_history[number] = []
                sent_history[number].append(otp_code)
                save_history(sent_history)
                
                flag, short_code = get_country_details(otp_entry.get("country", "Unknown"))
                send_styled_otp(number, flag, short_code, otp_code, service_tag, otp_full)
                print(f"✅ OTP Sent (Deletes in 90s)")
                        
    except Exception as e: 
        print(f"⚠️ Error: {e}")
    time.sleep(4)