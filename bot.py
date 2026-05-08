# -*- coding: utf-8 -*-
import telebot
import requests
import json
import pycountry
import threading
import time
import re
import os
from flask import Flask
from threading import Thread
from telebot import types
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

# --- RENDER KEEP-ALIVE SERVER ---
app = Flask('')

@app.route('/')
def home():
    return "Bot is Running Live!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()
# -------------------------------

# ---------------- CONFIG ----------------
BOT_TOKEN = "8510677584:AAG_tzm8V6zgrO89anNIurPyT0KSPdmg6Ns"
ADMIN_ID = 6136815573
ADMIN_USERNAME = "@PRINCE_SHUVO_75"
OTP_GROUP_LINK = "https://t.me/tem_withh"
API_KEY = "M_SX44INH5S"
API_BASE = "https://stexsms.com/mapi/v1/public"

CHANNELS = ["range_channele"] 
FIREBASE_URL = "https://realtime-database-7310e-default-rtdb.firebaseio.com/users"

# বাটন সেভ করার ফাইল
DB_FILE = "buttons_db.json"

if os.path.exists(DB_FILE):
    with open(DB_FILE, "r") as f:
        services_db = json.load(f)
else:
    services_db = {}
# ----------------------------------------

bot = telebot.TeleBot(BOT_TOKEN)
user_active_sessions = {}
pending_withdraws = {}

def save_db():
    with open(DB_FILE, "w") as f:
        json.dump(services_db, f)

# --- চ্যানেল জয়েন চেক ফাংশন ---
def is_joined(user_id):
    if user_id == ADMIN_ID: return True
    for channel in CHANNELS:
        try:
            member = bot.get_chat_member(f"@{channel}", user_id)
            if member.status in ["left", "kicked"]:
                return False
        except:
            return False
    return True

def force_join_markup():
    markup = InlineKeyboardMarkup(row_width=1)
    for channel in CHANNELS:
        markup.add(InlineKeyboardButton(f"📢 Join Channel", url=f"https://t.me/{channel}"))
    markup.add(InlineKeyboardButton("✅ Verify", callback_data="check_verify"))
    return markup

# --- অনলাইন ডাটাবেস ফাংশন ---
def get_user_balance(user_id):
    try:
        res = requests.get(f"{FIREBASE_URL}/{user_id}/balance.json", timeout=10)
        if res.status_code == 200 and res.json() is not None:
            return float(res.json())
    except: pass
    return 0.0

def update_user_balance(user_id, amount):
    current = get_user_balance(user_id)
    new_bal = round(current + amount, 2)
    try:
        requests.put(f"{FIREBASE_URL}/{user_id}/balance.json", data=json.dumps(new_bal), timeout=10)
    except: pass
    return new_bal

def get_all_users():
    try:
        res = requests.get(f"{FIREBASE_URL}.json", timeout=10)
        if res.status_code == 200 and res.json() is not None:
            return res.json().keys()
    except: pass
    return []

def main_keyboard():
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2, one_time_keyboard=False)
    markup.add(
        KeyboardButton("📱 Get Number"), 
        KeyboardButton("💰 Balance"),
        KeyboardButton("💸 Withdraw"), 
        KeyboardButton("👨‍💼 ADMIN SUPPORT")
    )
    return markup

def get_auto_flag(country_name):
    try:
        manual_flags = {"Ivory Coast": "🇨🇮", "Bangladesh": "🇧🇩", "Guinea": "🇬🇳", "Nepal": "🇳🇵"}
        if country_name in manual_flags: return manual_flags[country_name]
        country = pycountry.countries.search_fuzzy(country_name)[0]
        return "".join(chr(127397 + ord(c)) for c in country.alpha_2)
    except: return "🚩"

def fetch_single_number(rng):
    try:
        url = f"{API_BASE}/getnum/number"
        headers = {"mapikey": API_KEY, "Content-Type": "application/json"}
        payload = {"range": rng, "is_national": False, "remove_plus": False}
        res = requests.post(url, headers=headers, data=json.dumps(payload), timeout=15).json()
        return res.get("data", {})
    except: return {}

def check_otp_from_list(target_number):
    try:
        url = f"{API_BASE}/numsuccess/info"
        headers = {"mapikey": API_KEY}
        res = requests.get(url, headers=headers, timeout=10).json()
        if res.get("meta", {}).get("status") == "success":
            otps = res.get("data", {}).get("otps", [])
            clean_target = re.sub(r'\D', '', str(target_number))
            for item in otps:
                clean_api_num = re.sub(r'\D', '', str(item.get("number")))
                if clean_target in clean_api_num:
                    full_otp_text = str(item.get("otp"))
                    otp_only = re.findall(r'\d{4,8}', full_otp_text)
                    return otp_only[0] if otp_only else full_otp_text
    except: pass
    return None

# --- অ্যাডমিন বাটন ম্যানেজমেন্ট ---
@bot.message_handler(commands=['add'])
def add_button(msg):
    if msg.chat.id != ADMIN_ID: return
    try:
        data = msg.text.replace("/add", "").strip()
        name, rng = data.split(":")
        services_db[name.strip()] = rng.strip()
        save_db()
        bot.reply_to(msg, f"✅ বাটন অ্যাড হয়েছে: {name.strip()}")
    except:
        bot.reply_to(msg, "❌ ফরম্যাট: `/add Name : RangeID`")

@bot.message_handler(commands=['del'])
def delete_button(msg):
    if msg.chat.id != ADMIN_ID: return
    name = msg.text.replace("/del", "").strip()
    if name in services_db:
        del services_db[name]
        save_db()
        bot.reply_to(msg, f"🗑 '{name}' ডিলিট হয়েছে।")
    else:
        bot.reply_to(msg, "❌ বাটন পাওয়া যায়নি।")

# --- ব্রডকাস্ট লজিক ---
@bot.message_handler(commands=['users'])
def count_users(msg):
    if msg.chat.id != ADMIN_ID: return
    users = get_all_users()
    bot.reply_to(msg, f"👥 Total Registered Users: {len(list(users))}")

@bot.message_handler(commands=['send'])
def broadcast_handler(msg):
    if msg.chat.id != ADMIN_ID: return
    command_text = msg.text.replace("/send", "").strip()
    if not command_text:
        bot.reply_to(msg, "❌ কমান্ডের সাথে মেসেজটি লিখুন।")
        return
    users = get_all_users()
    sent, failed = 0, 0
    status_msg = bot.reply_to(msg, "⏳ মেসেজ পাঠানো শুরু হয়েছে...")
    for user_id in users:
        try:
            bot.send_message(user_id, command_text)
            sent += 1
            time.sleep(0.05)
        except: failed += 1
    bot.edit_message_text(f"✅ ব্রডকাস্ট সম্পন্ন!\n\n🚀 সফল: {sent}\n❌ ব্যর্থ: {failed}", msg.chat.id, status_msg.message_id)

# --- হ্যান্ডলারস ---
@bot.message_handler(commands=['start'])
def start(msg):
    user_id = msg.chat.id
    if not is_joined(user_id):
        bot.send_message(user_id, "⚠️ এই বটটি ব্যবহার করতে আমাদের চ্যানেলে জয়েন করুন।", reply_markup=force_join_markup())
        return
    get_user_balance(user_id)
    bot.send_message(user_id, f"👋 WELCOME {msg.from_user.first_name}!\n\n🧩 PLEASE SELECT A BUTTON BELOW:", reply_markup=main_keyboard())

@bot.message_handler(func=lambda m: m.text == "💰 Balance")
def check_balance(msg):
    if not is_joined(msg.chat.id):
        bot.send_message(msg.chat.id, "⚠️ প্রথমে চ্যানেলে জয়েন করুন।", reply_markup=force_join_markup())
        return
    bal = get_user_balance(msg.chat.id)
    bot.send_message(msg.chat.id, f"💰 Your Balance: {bal:.2f} ৳", reply_markup=main_keyboard())

@bot.message_handler(func=lambda m: m.text == "💸 Withdraw")
def withdraw_request(msg):
    if not is_joined(msg.chat.id):
        bot.send_message(msg.chat.id, "⚠️ প্রথমে চ্যানেলে জয়েন করুন।", reply_markup=force_join_markup())
        return
    if get_user_balance(msg.chat.id) < 50.0:
        bot.send_message(msg.chat.id, "❌ Minimum withdraw 50৳", reply_markup=main_keyboard())
        return
    bot.register_next_step_handler(bot.send_message(msg.chat.id, "টাকা তোলার পরিমাণ (Amount) লিখুন:", reply_markup=main_keyboard()), ask_bkash_number)

def ask_bkash_number(msg):
    try:
        amount = float(msg.text)
        bot.register_next_step_handler(bot.send_message(msg.chat.id, "আপনার বিকাশ নাম্বারটি দিন:", reply_markup=main_keyboard()), finalize_withdraw, amount)
    except: bot.send_message(msg.chat.id, "❌ সঠিক সংখ্যা লিখুন।", reply_markup=main_keyboard())

def finalize_withdraw(msg, amount):
    user_id, user_name, b_num = msg.chat.id, msg.from_user.first_name, msg.text.strip()
    rid = str(time.time()).replace('.', '')
    pending_withdraws[rid] = {"user_id": user_id, "amount": amount}
    kb = InlineKeyboardMarkup().add(InlineKeyboardButton("✅ Approve", callback_data=f"approve_{rid}"), InlineKeyboardButton("❌ Reject", callback_data=f"reject_{rid}"))
    
    admin_msg = (
f"╔══════════════════════╗\n"
f"   💸 <b>NEW PAYMENT REQUEST</b>   \n"
f"╚══════════════════════╝\n\n"
f"👤 <b>User:</b> {user_name}\n"
f"🆔 <b>ID:</b> <code>{user_id}</code>\n"
f"💰 <b>Amount:</b> {amount}৳\n"
f"📞 <b>Bkash:</b> <code>{b_num}</code>\n\n"
f"──────────────────────\n"
f"💡 <i>Status: Pending Approval</i>\n"
f"──────────────────────"
    )
    bot.send_message(user_id, "⏳ রিকোয়েস্টটি এডমিনের কাছে পাঠানো হয়েছে।", reply_markup=main_keyboard())
    bot.send_message(ADMIN_ID, admin_msg, reply_markup=kb, parse_mode="HTML")

@bot.message_handler(func=lambda m: m.text == "👨‍💼 ADMIN SUPPORT")
def admin_support(msg):
    if not is_joined(msg.chat.id):
        bot.send_message(msg.chat.id, "⚠️ প্রথমে চ্যানেলে জয়েন করুন।", reply_markup=force_join_markup())
        return
    kb = InlineKeyboardMarkup().add(InlineKeyboardButton("📩 Contact Admin", url=f"tg://user?id={ADMIN_ID}"))
    
    support_msg = (
f"<b>╔══════════════════════╗\n"
f"     👨‍💼 ADMIN SUPPORT     \n"
f"╚══════════════════════╝</b>\n\n"
f"➜ আপনার কোনো সমস্যা বা প্রশ্ন থাকলে\n"
f"সরাসরি এডমিনের সাথে যোগাযোগ করুন।\n\n"
f"━━━━━━━━━━━━━━━━━━━━\n"
f"👤 Admin সাথে কথা বলতে\n"
f"নিচের বাটনে ক্লিক করুন 👇\n"
f"━━━━━━━━━━━━━━━━━━━━"
    )
    bot.send_message(msg.chat.id, support_msg, reply_markup=kb, parse_mode="HTML")

@bot.message_handler(func=lambda m: m.text == "📱 Get Number")
def ask_range(msg):
    if not is_joined(msg.chat.id):
        bot.send_message(msg.chat.id, "⚠️ প্রথমে চ্যানেলে জয়েন করুন।", reply_markup=force_join_markup())
        return
    
    markup = InlineKeyboardMarkup(row_width=2)
    buttons = [InlineKeyboardButton(name, callback_data=f"stex_{rng}") for name, rng in services_db.items()]
    
    if buttons:
        markup.add(*buttons)
        m_txt = (
        "╔══════════════════════╗\n"
        "     🚀 SYSTEM READY     \n"
        "╚══════════════════════╝\n\n"
        "➜ সার্ভিস সিলেক্ট করুন নিচে থেকে\n"
        "──────────────────────\n"
        "💡 Status: Waiting for selection...\n"
        "──────────────────────"
        )
    else:
        m_txt = "NO NUMBER UPLOAD ❌"

    bot.send_message(msg.chat.id, m_txt, reply_markup=markup)

# --- নম্বর সেন্ডিং ফাংশন ---
def fetch_and_send_numbers(chat_id, rng, message_id=None):
    try:
        if chat_id in user_active_sessions:
            user_active_sessions[chat_id]['sid'] = 0
        data1, data2 = fetch_single_number(rng), fetch_single_number(rng)
        num1, num2 = data1.get("full_number") or data1.get("number"), data2.get("full_number") or data2.get("number")
        country = data1.get("country") or "Unknown"
        flag = get_auto_flag(country)
        if num1 or num2:
            d1, d2 = (str(num1).replace('+', '') if num1 else "No stock"), (str(num2).replace('+', '') if num2 else "No stock")
            sid = time.time()
            user_active_sessions[chat_id] = {'sid': sid, 'range': rng, 'n1': d1, 'n2': d2, 'c': country, 'f': flag, 'ids': []}
            text = f"✅ **Number Successfully Assigned!**\n\n🌎 {country} {flag}\n🛠 **Service:** Facebook"
            markup = InlineKeyboardMarkup(row_width=1)
            if d1 != "No stock":
                markup.add(InlineKeyboardButton(text=f"{flag} {d1}", copy_text=types.CopyTextButton(text=d1)))
            if d2 != "No stock":
                markup.add(InlineKeyboardButton(text=f"{flag} {d2}", copy_text=types.CopyTextButton(text=d2)))

            markup.add(InlineKeyboardButton(text="🔄 Change Number", callback_data="change_direct"),
                       InlineKeyboardButton(text="🔑 View OTP Group", url=OTP_GROUP_LINK))
            
            if message_id:
                bot.edit_message_text(text, chat_id, message_id, reply_markup=markup, parse_mode="Markdown")
            else:
                bot.send_message(chat_id, text, reply_markup=markup, parse_mode="Markdown")
            threading.Thread(target=auto_otp_worker, args=(chat_id, sid), daemon=True).start()
        else: 
            bot.send_message(chat_id, "⚠️ এই রেঞ্জে নম্বর পাওয়া যায়নি।")
    except: pass

@bot.callback_query_handler(func=lambda call: True)
def handle_callbacks(call):
    chat_id = call.message.chat.id
    if call.data == "check_verify":
        if is_joined(call.from_user.id):
            bot.answer_callback_query(call.id, "✅ Verified!", show_alert=True)
            bot.delete_message(chat_id, call.message.message_id)
            start(call.message)
        else: bot.answer_callback_query(call.id, "❌ আপনি এখনো চ্যানেলে জয়েন করেননি!", show_alert=True)
    
    elif call.data.startswith("stex_"):
        rng = call.data.split("_")[1]
        fetch_and_send_numbers(chat_id, rng, call.message.message_id)

    elif call.data == "change_direct":
        rng = user_active_sessions.get(chat_id, {}).get('range')
        if rng: fetch_and_send_numbers(chat_id, rng, call.message.message_id)
        
    elif "_" in call.data and chat_id == ADMIN_ID:
        action, rid = call.data.split("_")
        data = pending_withdraws.get(rid)
        if data:
            uid, amt = data["user_id"], data["amount"]
            if action == "approve":
                update_user_balance(uid, -amt)
                bot.send_message(uid, f"✅ আপনার {amt}৳ পেমেন্ট রিকোয়েস্টটি এপ্রুভ হয়েছে।", reply_markup=main_keyboard())
            else: bot.send_message(uid, f"❌ আপনার {amt}৳ রিকোয়েস্টটি রিজেক্ট হয়েছে।", reply_markup=main_keyboard())
            pending_withdraws.pop(rid, None)
            bot.delete_message(chat_id, call.message.message_id)

def auto_otp_worker(chat_id, sid):
    while True:
        data = user_active_sessions.get(chat_id)
        if not data or data.get('sid') != sid: break
        for cn in [data.get('n1'), data.get('n2')]:
            if cn != "No stock":
                otp = check_otp_from_list(cn)
                if otp and f"{cn}_{otp}" not in data['ids']:
                    data['ids'].append(f"{cn}_{otp}")
                    update_user_balance(chat_id, 0.20)
                    
                    otp_msg = (
                        f"━━━━━━━━━━━━━━━\n"
                        f"📩 <b>NEW OTP RECEIVED</b>\n"
                        f"━━━━━━━━━━━━━━━\n"
                        f"🌍 Country: {data['c']} {data['f']}\n"
                        f"📱 Number: <code>{cn}</code>\n"
                        f"🔑 OTP Code: <code>{otp}</code>\n"
                        f"━━━━━━━━━━━━━━━\n"
                        f"💰 Earned: <b>+0.20৳</b>\n"
                        f"━━━━━━━━━━━━━━━"
                    )
                    bot.send_message(chat_id, otp_msg, parse_mode="HTML", reply_markup=main_keyboard())
        time.sleep(5)

if __name__ == "__main__":
    keep_alive() # এটি রেন্ডারে বটকে সচল রাখবে
    bot.remove_webhook()
    print("Bot is Starting...")
    bot.infinity_polling()
