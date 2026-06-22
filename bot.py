# -*- coding: utf-8 -*-

import telebot 
import requests 
import json 
import pycountry 
import threading 
import time 
import re 
import os 
import random
import logging
import traceback
from flask import Flask 
from threading import Thread 
from telebot import types 
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

# --- RENDER KEEP-ALIVE SERVER ---
app = Flask('')
@app.route('/') 
def home(): return "Bot is Running Live!"
def run_flask(): app.run(host='0.0.0.0', port=8080)
def keep_alive(): 
    t = Thread(target=run_flask, daemon=True)
    t.start()

# --- কনফিগারেশন ---
API_KEY = "MUBTR1MKUBO" 
BOT_TOKEN = "8510677584:AAHjTslHP_YokhEYxoqiYDW7i59cZbE3PkA" 
BASE_URL = "https://api.2oo9.cloud/MXS47FLFX0U/tness/@public/api" 
HEADERS = {"mauthapi": API_KEY} 
ADMIN_ID = "6136815573" 
GROUP_URL = "https://t.me/tem_withh"
FIREBASE_URL = "https://my-otp-bot-e8ef9-default-rtdb.firebaseio.com/" 

session = requests.Session() 
session.headers.update(HEADERS)

# --- FIREBASE LOGIC ---
def get_firebase_balance(uid):
    try:
        res = session.get(f"{FIREBASE_URL}/users/{uid}/balance.json")
        if res.status_code == 200 and res.json() is not None:
            return float(res.json())
    except: pass
    return 0.0

def update_firebase_balance(uid, amount):
    try:
        current = get_firebase_balance(uid)
        new_bal = round(current + amount, 2)
        session.put(f"{FIREBASE_URL}/users/{uid}/balance.json", data=json.dumps(new_bal))
        return new_bal
    except: return 0.0

# Firebase সার্ভিস লোড ও সেভ
def load_services_from_firebase():
    res = session.get(f"{FIREBASE_URL}/services.json")
    return res.json() if res.status_code == 200 and res.json() is not None else {}

def save_service_to_firebase(country, rid):
    session.put(f"{FIREBASE_URL}/services/{country}.json", data=json.dumps(rid))

# ===================== STABLE SESSION =====================
logging.basicConfig(level=logging.ERROR, format="%(asctime)s - %(levelname)s - %(message)s")
bot = telebot.TeleBot(BOT_TOKEN, threaded=True, num_threads=20)

user_ranges = {} 
user_numbers = {} 
user_countries = {} 
service_buttons = load_services_from_firebase()  # Firebase থেকে লোড হবে
users = {} 
withdraw_data = {} 
received_otps = {} 
REQUIRED_CHANNELS = ["@range_channele", "@tem_withh"] 
otp_running = {}   
used_otps = {} 

# ===================== GLOBAL ERROR PROTECTION =====================
def safe_execute(func): 
    def wrapper(*args, **kwargs): 
        try: return func(*args, **kwargs) 
        except Exception: logging.error(traceback.format_exc()) 
    return wrapper

def clean_number(num): return "".join(filter(str.isdigit, str(num)))

def get_flag(country_name): 
    try: 
        country = pycountry.countries.lookup(country_name) 
        code = country.alpha_2 
        return "".join(chr(ord(c) + 127397) for c in code.upper()) 
    except: return "🌍"

def is_joined(user_id): 
    try: 
        for channel in REQUIRED_CHANNELS: 
            member = bot.get_chat_member(channel, user_id) 
            if member.status not in ["member", "administrator", "creator"]: return False 
        return True 
    except: return False

def join_markup(): 
    kb = types.InlineKeyboardMarkup(row_width=1) 
    kb.add(types.InlineKeyboardButton("📢 Join Channel 1", url="https://t.me/range_channele")) 
    kb.add(types.InlineKeyboardButton("📢 Join Channel 2", url="https://t.me/tem_withh")) 
    kb.add(types.InlineKeyboardButton("✅ VERIFIED", callback_data="verify_join")) 
    return kb

@safe_execute 
@bot.message_handler(commands=['start']) 
def start(message): 
    if str(message.from_user.id) not in users: users[str(message.from_user.id)] = {"balance": 0}
        
    if not is_joined(message.from_user.id): 
        bot.send_message(message.chat.id, "⚠️ বট ব্যবহার করার আগে নিচের দুইটি চ্যানেলে Join করুন এবং তারপর VERIFIED বাটনে চাপুন।", reply_markup=join_markup()) 
        return 
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2) 
    markup.row(types.KeyboardButton("📱 𝙶𝙴𝚃 𝙽𝚄𝙼𝙱𝙴𝚁"), types.KeyboardButton("📱 𝙽𝚄𝙼𝙱𝙴𝚁 𝙱𝚄𝚈")) 
    markup.add(types.KeyboardButton("🔐 𝙶𝙴𝚃 2𝙵𝙰 𝙲𝙾𝙳𝙴"), types.KeyboardButton("👑 𝙰𝙳𝙼𝙸𝙽 𝚂𝚄𝙿𝙿𝙾𝚁𝚃"), types.KeyboardButton("👤 𝙿𝚁𝙾𝙵𝙸𝙻𝙴")) 
    
    welcome_text = (
        "👋𓆩𓆩𝚆𝙴𝙻𝙲𝙾𝙼𝙴 𝚃𝙾 𝙾𝚃𝙿 𝚂𝙴𝚁𝚅𝚒𝙲𝙴𓆪𓆪\n"
        "﹌﹌﹌﹌﹌﹌﹌﹌﹌﹌﹌﹌﹌﹌﹌\n\n"
        "🤖 𝚆𝙴𝙻𝙲𝙾𝙼𝙴 𝚃𝙾 𝚃𝙴𝙰𝙼 𝚆𝙸𝚃𝙷 3.0 𝙽𝚄𝙼𝙱𝙴𝚁 𝙱𝙾𝚃\n\n"
        "﹌﹌﹌﹌﹌﹌﹌﹌﹌﹌﹌﹌﹌﹌﹌\n\n"
        "♾️ 𝙿𝙾𝚆𝙴𝚁𝙴𝙳 𝙱𝚈 Shuvoᯓᡣ𐭩"
    )
    bot.send_message(message.chat.id, welcome_text, reply_markup=markup)

@bot.message_handler(commands=['user'])
def count_users(message):
    if str(message.from_user.id) == ADMIN_ID:
        bot.reply_to(message, f"👥 মোট ইউজার সংখ্যা: {len(users)}")

@bot.message_handler(commands=['send'])
def broadcast(message):
    if str(message.from_user.id) == ADMIN_ID:
        text = message.text.replace("/send", "", 1).strip()
        if not text:
            bot.reply_to(message, "⚠️ কিছু লিখুন। যেমন: /send হ্যালো!")
            return
        count = 0
        for uid in users:
            try:
                bot.send_message(uid, text)
                count += 1
            except: pass
        bot.reply_to(message, f"✅ {count} জন ইউজারকে মেসেজ পাঠানো হয়েছে।")

@bot.message_handler(commands=['add']) 
def add_service(message): 
    if str(message.from_user.id) != ADMIN_ID: return 
    text = message.text.replace("/add", "", 1).strip() 
    if ":" not in text: return 
    country, rid = text.split(":", 1) 
    country, rid = country.strip(), rid.strip()
    service_buttons[country] = rid
    save_service_to_firebase(country, rid)
    bot.reply_to(message, f"✅ Added Successfully\n🌍 Country : {country}\n🔢 Range : {rid}")

@bot.message_handler(commands=['del']) 
def del_service(message): 
    if str(message.from_user.id) != ADMIN_ID: return 
    key = message.text.replace("/del", "", 1).strip().lower() 
    for country in list(service_buttons.keys()): 
        if key in country.lower(): 
            del service_buttons[country] 
            session.delete(f"{FIREBASE_URL}/services/{country}.json")
            bot.reply_to(message, f"✅ {country} Deleted Successfully.") 
            break

@bot.message_handler(commands=['addmoney']) 
def add_money_by_admin(message): 
    if str(message.from_user.id) != ADMIN_ID: return 
    parts = message.text.split()
    if len(parts) != 3:
        bot.reply_to(message, "⚠️ ভুল ফরম্যাট! সঠিক নিয়ম:\n/addmoney [user_id] [amount]")
        return
    uid = parts[1]
    amount = float(parts[2])
    new_bal = update_firebase_balance(uid, amount)
    bot.reply_to(message, f"✅ সফলভাবে ব্যালেন্স আপডেট হয়েছে!\n👤 ইউজার ID: {uid}\n💰 নতুন ব্যালেন্স: {new_bal} 𝚃𝙺")

# --- OTP SEARCH & BALANCE ---
def auto_check_otp(chat_id, phone_number, country, search_msg_id=None): 
    if otp_running.get(chat_id): return 
    otp_running[chat_id] = True 
    start_time = time.time() 
    try: 
        while time.time() - start_time < 120: 
            response = session.get(f"{BASE_URL}/success-otp", timeout=10) 
            data = response.json() 
            if data.get("meta", {}).get("code") == 200: 
                for item in data.get("data", {}).get("otps", []): 
                    msg_id = item.get("id")
                    if clean_number(item.get("number")) in clean_number(phone_number) and msg_id not in used_otps.get(chat_id, []): 
                        if chat_id not in used_otps: used_otps[chat_id] = []
                        used_otps[chat_id].append(msg_id)
                        
                        otp = "".join(filter(str.isdigit, item.get("message", "")))[-6:] 
                        received_otps[chat_id] = otp
                        new_bal = update_firebase_balance(chat_id, 0.15)
                        
                        text = (
                            "╔════════════════════╗\n"
                            f"    ➤ {phone_number} ➤ 𝚁𝙲𝚅𝙴𝙳 ✅\n"
                            "╚════════════════════╝\n"
                            "💰 𝙱𝚊𝚕𝚊𝚗𝚌𝚎 𝙰𝚍𝚍𝚎𝚍: +0.15 𝚃𝙺  \n"
                            f"🏦 𝚃𝚘𝚝𝚊𝚕 𝙱𝚊𝚕𝚊𝚗𝚌𝚎: {new_bal:.2f} 𝚃𝙺"
                        )
                        
                        kb = types.InlineKeyboardMarkup() 
                        kb.add(types.InlineKeyboardButton(text=otp, copy_text=types.CopyTextButton(text=otp))) 
                        
                        if search_msg_id: bot.edit_message_text(text, chat_id, search_msg_id, parse_mode="Markdown", reply_markup=kb) 
                        else: bot.send_message(chat_id, text, parse_mode="Markdown", reply_markup=kb) 
                        return 
            time.sleep(2) 
        if search_msg_id: 
            kb = types.InlineKeyboardMarkup() 
            kb.add(types.InlineKeyboardButton("🔄 TRY AGAIN", callback_data="otp_search")) 
            bot.edit_message_text("❌ 𝙽𝚘 𝙾𝚃𝙿 𝙵𝚘𝚞𝚗𝚍", chat_id, search_msg_id, reply_markup=kb) 
    finally: otp_running[chat_id] = False

# --- NUMBER PROCESSING ---
def process_number(message, edit_msg=None): 
    rid = message.text 
    if edit_msg: bot.edit_message_text("⏳ 𝙿𝙻𝙴𝙰𝚂𝙴 𝚆𝙰𝙸𝚃...\n🔄 𝙽𝚄𝙼𝙱𝙴𝚁 𝙶𝙴𝙽𝙴𝚁𝙰𝚃𝙸𝙽𝙶...", message.chat.id, edit_msg.message_id); status_id = edit_msg.message_id 
    else: status_id = bot.send_message(message.chat.id, "⏳ 𝙿𝙻𝙴𝙰𝚂𝙴 𝚆𝙰𝙸𝚃...\n🔄 𝙽𝚄𝙼𝙱𝙴𝚁 𝙶𝙴𝙽𝙴𝚁𝙰𝚃𝙸𝙽𝙶...").message_id
    try: 
        response = session.post(f"{BASE_URL}/getnum", json={"rid": rid}, timeout=15) 
        data = response.json() 
        if data.get("meta", {}).get("code") == 200: 
            full_num = str(data.get("data", {}).get("full_number")).replace("+", "") 
            country = data.get("data", {}).get("country", "Unknown") 
            user_numbers[message.chat.id] = full_num; user_countries[message.chat.id] = country; user_ranges[message.chat.id] = rid 
            received_otps[message.chat.id] = None
            kb = types.InlineKeyboardMarkup(row_width=2) 
            kb.add(types.InlineKeyboardButton(text=f"+{full_num}", copy_text=types.CopyTextButton(text=f"+{full_num}"))) 
            kb.row(types.InlineKeyboardButton("🔄 𝙲𝚑𝚊𝚗𝚐𝚎 𝙽𝚞𝚖𝚋𝚎𝚛", callback_data="change_num"), types.InlineKeyboardButton("🔍 𝙾𝚃𝙿 𝚂𝙴𝙰𝚁𝙲𝙷", callback_data="otp_search")) 
            kb.add(types.InlineKeyboardButton("🔐 𝙾𝚃𝙿 𝙶𝚁𝙾𝚄𝙿", url=GROUP_URL)) 
            msg = ("✅ 𝙽𝚞𝚖𝚋𝚎𝚛 𝙰𝚜𝚜𝚒𝚐𝚗𝚎𝚍 !\n━━━━━━━━━━━━━━━━━━━━\n\n" f"🟢 𝙲𝚘𝚞𝚗𝚝𝚛𝚢 : {get_flag(country)} {country}\n\n📞 𝙽𝚞𝚖𝚋𝚎𝚛 : {full_num}\n\n" "🌺 𝚂𝚎𝚛𝚟𝚒𝚌𝚎 : 𝙵𝚊𝚌𝚎𝚋𝚘𝚘𝚔\n\n━━━━━━━━━━━━━━━━━━━━\n⏳ 𝚆𝙰𝙸𝚃𝙸𝙽𝙶 𝙵𝙾𝚁 𝙾𝚃𝙿...") 
            bot.edit_message_text(msg, message.chat.id, status_id, parse_mode="Markdown", reply_markup=kb) 
            threading.Thread(target=auto_check_otp, args=(message.chat.id, full_num, country), daemon=True).start()
        else: bot.edit_message_text("❌ নাম্বার পাওয়া যায়নি!", message.chat.id, status_id) 
    except Exception as e: bot.edit_message_text(f"❌ ত্রুটি: {e}", message.chat.id, status_id)

@safe_execute 
@bot.message_handler(func=lambda message: True) 
def handle_text(message): 
    if str(message.from_user.id) not in users: users[str(message.from_user.id)] = {"balance": 0}
        
    if not is_joined(message.from_user.id): 
        bot.send_message(message.chat.id, "⚠️ দয়া করে চ্যানেলে জয়েন করুন।", reply_markup=join_markup()) 
        return 
    if message.text == "📱 𝙽𝚄𝙼𝙱𝙴𝚁 𝙱𝚄𝚈": 
        msg = bot.send_message(message.chat.id, "⚙️ 𝙿𝙻𝙴𝙰𝚂𝙴 𝙴𝙽𝚃𝙴𝚁 𝚈𝙾𝚄𝚁 𝚁𝙰𝙽𝙶𝙴\n\n🔢 𝙴𝚡𝚊𝚖𝚙𝚕𝚎 : 2245564", parse_mode="Markdown") 
        bot.register_next_step_handler(msg, process_number) 
    elif message.text == "📱 𝙶𝙴𝚃 𝙽𝚄𝙼𝙱𝙴𝚁": 
        kb = types.InlineKeyboardMarkup(row_width=1) 
        for country in service_buttons: 
            kb.add(types.InlineKeyboardButton(text=f"{get_flag(country)} {country}", callback_data=f"service_{country}")) 
        bot.send_message(message.chat.id, "🟢 𝘾𝙝𝙤𝙤𝙨𝙚 𝙎𝙚𝙧𝙫𝙞𝙘𝙚 🟢", reply_markup=kb) 
    elif message.text == "🔐 𝙶𝙴𝚃 2𝙵𝙰 𝙲𝙾𝙳𝙴": 
        msg = bot.send_message(message.chat.id, "🔐 𝙿𝙻𝙴𝙰𝚂𝙴 𝙴𝙽𝚃𝙴𝚁 𝚈𝙾𝚄𝚁 𝟸𝙵𝙰 𝙺𝙴𝚈") 
        bot.register_next_step_handler(msg, process_2fa) 
    elif message.text == "👤 𝙿𝚁𝙾𝙵𝙸𝙻𝙴": 
        user_id = str(message.from_user.id)
        balance = get_firebase_balance(user_id)
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🏦 𝚆𝙸𝚃𝙷𝙳𝚁𝙰𝚆", callback_data="withdraw"))
        msg = (
            "╔════════════════════╗\n"
            "      👤 𝚄𝚂𝙴𝚁 𝙿𝚁𝙾𝙵𝙸𝙻𝙴\n"
            "╚════════════════════╝\n\n"
            f"🆔 𝙸𝙳 : {user_id}  \n"
            f"💰 𝙱𝙰𝙻𝙰𝙽𝙲𝙴 : {balance:.2f}$\n\n"
            "✅ 𝚂𝚃𝙰𝚃𝚄𝚂 : 𝙰𝙲𝚃𝙸𝚅𝙴"
        )
        bot.send_message(message.chat.id, msg, reply_markup=markup)
    elif message.text == "👑 𝙰𝙳𝙼𝙸𝙽 𝚂𝚄𝙿𝙿𝙾𝚁𝚃": 
        kb = types.InlineKeyboardMarkup() 
        kb.add(types.InlineKeyboardButton("📩 এডমিনকে মেসেজ দিন", url=f"tg://user?id={ADMIN_ID}")) 
        bot.send_message(message.chat.id, "💬 যেকোনো সমস্যার জন্য এডমিনকে মেসেজ দিন।", reply_markup=kb)

def process_2fa(message): 
    code = str(random.randint(100000, 999999)) 
    kb = types.InlineKeyboardMarkup() 
    kb.add(types.InlineKeyboardButton(text=code, copy_text=types.CopyTextButton(text=code))) 
    bot.send_message(message.chat.id, f"🔐 𝚈𝙾𝚄𝚁 𝟸𝙵𝙰 𝙲𝙾𝙳𝙴 ✅\n\n{code}", parse_mode="Markdown", reply_markup=kb)

@safe_execute 
@bot.callback_query_handler(func=lambda call: True) 
def handle_query(call): 
    if call.data == "verify_join": 
        if is_joined(call.from_user.id): bot.answer_callback_query(call.id, "✅ You are verified!"); start(call.message) 
        else: bot.answer_callback_query(call.id, "❌ Still not joined!") 
    elif call.data == "change_num": 
        rid = user_ranges.get(call.message.chat.id) 
        if not rid: return 
        fake_msg = type("obj", (object,), {"chat": call.message.chat, "text": rid})() 
        process_number(fake_msg, edit_msg=call.message) 
    elif call.data == "otp_search": 
        if otp_running.get(call.message.chat.id): bot.answer_callback_query(call.id, "⏳ OTP Search Already Running!"); return 
        
        if received_otps.get(call.message.chat.id):
            msg = (
                "╔════════════════════╗\n"
                "      ✦ 𝙾𝚃𝙿 𝚁𝙲𝚅 ✦\n"
                "╚════════════════════╝\n\n"
                "➤ OTP ➤ 𝙰𝚕𝚛𝚎𝚊𝚍𝚢 𝚁𝚎𝚌𝚟𝚎𝚒𝚟𝚎𝚍 ✅\n\n"
                "💎 𝚂𝚝𝚊𝚝𝚞𝚜: 𝙰𝚌𝚝𝚒𝚟𝚎\n"
                "🏦 𝚂𝚎𝚛𝚟𝚒𝚌𝚎: 𝙾𝚃𝙿 𝚄𝚗𝚕𝚘𝚌𝚔𝚎𝚍"
            )
            bot.send_message(call.message.chat.id, msg)
        else:
            user_num = user_numbers.get(call.message.chat.id); country = user_countries.get(call.message.chat.id, "Unknown") 
            search_msg = bot.send_message(call.message.chat.id, "🔍 𝙾𝚃𝙿 𝚂𝙴𝙰𝚁𝙲𝙷𝙸𝙽𝙶...\n\n⏳ 𝙿𝚕𝚎𝚊𝚜𝚎 𝚆𝚊𝚒𝚝...") 
            threading.Thread(target=auto_check_otp, args=(call.message.chat.id, user_num, country, search_msg.message_id), daemon=True).start() 
    elif call.data.startswith("service_"): 
        country = call.data.replace("service_", "", 1); rid = service_buttons.get(country) 
        if not rid: return 
        user_ranges[call.message.chat.id] = rid 
        fake_msg = type("obj", (object,), {"chat": call.message.chat, "text": rid})() 
        process_number(fake_msg)
    elif call.data == "withdraw":
        balance = get_firebase_balance(call.from_user.id)
        if balance < 20: bot.answer_callback_query(call.id, "❌ Min 20 TK!"); return
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(types.InlineKeyboardButton("💳 𝙱𝙺𝙰𝚂𝙷", callback_data="bkash"), types.InlineKeyboardButton("💳 𝚁𝙾𝙲𝙺𝙴𝚃", callback_data="rocket"))
        bot.edit_message_text("🏦 𝚂𝙴𝙻𝙴𝙲𝚃 𝙿𝙰𝚈𝙼𝙴𝙽𝚃 𝙼𝙴𝚃𝙷𝙾𝙳", call.message.chat.id, call.message.message_id, reply_markup=markup)
    elif call.data in ["bkash", "rocket"]:
        withdraw_data[call.from_user.id] = {"method": call.data.capitalize()}
        msg = bot.send_message(call.message.chat.id, f"📱 𝙴𝙽𝚃𝙴𝚁 𝚈𝙾𝚄𝚁 {call.data.upper()} 𝙽𝚄𝙼𝙱𝙴𝚁")
        bot.register_next_step_handler(msg, get_number)
    elif call.data.startswith("approve_"):
        uid = call.data.split("_")[1]
        amount = withdraw_data.get(int(uid), {}).get("amount", 0)
        update_firebase_balance(uid, -amount)
        bot.send_message(uid, "✅ 𝙿𝙰𝚈𝙼𝙴𝙽𝚃 𝚂𝚄𝙲𝙲𝙴𝚂𝚂!")
        bot.edit_message_text("✅ Approved", call.message.chat.id, call.message.message_id)

def get_number(message):
    withdraw_data[message.from_user.id]["number"] = message.text
    msg = bot.send_message(message.chat.id, "💰 𝙴𝙽𝚃𝙴𝚁 𝙰𝙼𝙾𝚄𝙽𝚃 (𝙼𝙸𝙽 20 𝚃𝙺)")
    bot.register_next_step_handler(msg, get_amount)

def get_amount(message):
    try:
        amount = int(message.text)
        if amount < 20: bot.send_message(message.chat.id, "❌ Minimum 20 TK!"); return
        withdraw_data[message.from_user.id]["amount"] = amount
        admin_text = f"💸 𝙽𝙴𝚆 𝙿𝙰𝚈𝙼𝙴𝙽𝚃 𝚁𝙴𝚀𝚄𝙴𝚂𝚃\n👤 𝙸𝙳 : {message.from_user.id}\n💰 𝙰𝙼𝙾𝚄𝙽𝚃 : {amount}\n📱 {withdraw_data[message.from_user.id]['method']} : {withdraw_data[message.from_user.id]['number']}"
        markup = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("✅ 𝙰𝙿𝙿𝚁𝙾𝚅𝙴", callback_data=f"approve_{message.from_user.id}"))
        bot.send_message(ADMIN_ID, admin_text, reply_markup=markup)
        bot.send_message(message.chat.id, "✅ 𝚂𝚄𝙱𝙼𝙸𝚃𝚃𝙴𝙳!")
    except: bot.send_message(message.chat.id, "❌ Error!")

def run_bot(): 
    keep_alive() 
    while True: 
        try: 
            bot.polling(none_stop=True, interval=0, timeout=60, long_polling_timeout=60)
        except Exception: 
            time.sleep(2) 

if __name__ == "__main__": 
    run_bot()
