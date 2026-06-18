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
import firebase_admin
from firebase_admin import credentials, db
from flask import Flask 
from threading import Thread 
from telebot import types 
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

# --- FIREBASE SETUP ---
# এই ফাইলটি (serviceAccountKey.json) আপনার বটের ফোল্ডারে অবশ্যই থাকতে হবে
cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred, {'databaseURL': 'https://your-database-name.firebaseio.com/'})
db_ref = db.reference('users_data')

# --- RENDER KEEP-ALIVE SERVER ---
app = Flask('')
@app.route('/') 
def home(): return "Bot is Running Live!"
def run_flask(): app.run(host='0.0.0.0', port=8080)
def keep_alive(): t = Thread(target=run_flask); t.start()

# --- কনফিগারেশন ---
API_KEY = "MUBTR1MKUBO" 
BOT_TOKEN = "8510677584:AAFhQUDpKMCibXymV6di4gB-1kWHX-FEPNE" 
BASE_URL = "https://api.2oo9.cloud/MXS47FLFX0U/tness/@public/api" 
HEADERS = {"mauthapi": API_KEY} 
ADMIN_ID = "6136815573" 
GROUP_URL = "https://t.me/tem_withh"

# ===================== STABLE SESSION =====================
session = requests.Session() 
session.headers.update(HEADERS)
logging.basicConfig(level=logging.ERROR, format="%(asctime)s - %(levelname)s - %(message)s")
bot = telebot.TeleBot(BOT_TOKEN, threaded=True, num_threads=20)

user_ranges = {} 
user_numbers = {} 
user_countries = {} 
service_buttons = {}  
users = {} 
withdraw_data = {} 
REQUIRED_CHANNELS = ["@range_channele", "@tem_withh"] 
otp_running = {}   

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
    db_ref.child(str(message.from_user.id)).update({"active": True})
    if not is_joined(message.from_user.id): 
        bot.send_message(message.chat.id, "⚠️ বট ব্যবহার করার আগে নিচের দুইটি চ্যানেলে Join করুন এবং তারপর VERIFIED বাটনে চাপুন।", reply_markup=join_markup()) 
        return 
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2) 
    markup.row(types.KeyboardButton("📱 𝙶𝙴𝚃 𝙽𝚄𝙼𝙱𝙴𝚁"), types.KeyboardButton("📱 𝙽𝚄𝙼𝙱𝙴𝚁 𝙱𝚄𝚈")) 
    markup.add(types.KeyboardButton("🔐 𝙶𝙴𝚃 2𝙵𝙰 𝙲𝙾𝙳𝙴"), types.KeyboardButton("👑 𝙰𝙳𝙼𝙸𝙽 𝚂𝚄𝙿𝙿𝙾𝚁𝚃"), types.KeyboardButton("👤 𝙿𝚁𝙾𝙵𝙸𝙻𝙴")) 
    welcome_text = "👋𓆩𓆩𝚆𝙴𝙻𝙲𝙾𝙼𝙴 𝚃𝙾 𝙾𝚃𝙿 𝚂𝙴𝚁𝚅𝙸𝙲𝙴𓆪𓆪\n\n🤖 𝚆𝙴𝙻𝙲𝙾𝙼𝙴 𝚃𝙾 𝚃𝙴𝙰𝙼 𝚆𝙸𝚃𝙷 3.0 𝙽𝚄𝙼𝙱𝙴𝚁 𝙱𝙾𝚃\n\n♾️ 𝙿𝙾𝚆𝙴𝚁𝙴𝙳 𝙱𝚈 Shuvoᯓᡣ𐭩"
    bot.send_message(message.chat.id, welcome_text, reply_markup=markup)

@bot.message_handler(commands=['user'])
def count_users(message):
    if str(message.from_user.id) == ADMIN_ID:
        count = len(db_ref.get() or {})
        bot.reply_to(message, f"👥 মোট ইউজার সংখ্যা: {count}")

@bot.message_handler(commands=['send'])
def broadcast(message):
    if str(message.from_user.id) == ADMIN_ID:
        text = message.text.replace("/send", "").strip()
        for uid in (db_ref.get() or {}):
            try: bot.send_message(uid, text)
            except: pass

@bot.message_handler(commands=['add']) 
def add_service(message): 
    if str(message.from_user.id) != ADMIN_ID: return 
    text = message.text.replace("/add", "", 1).strip() 
    if ":" not in text: return 
    country, rid = text.split(":", 1) 
    service_buttons[country.strip()] = rid.strip() 
    bot.reply_to(message, f"✅ Added Successfully\n🌍 Country : {country.strip()}\n🔢 Range : {rid.strip()}")

@bot.message_handler(commands=['del']) 
def del_service(message): 
    if str(message.from_user.id) != ADMIN_ID: return 
    key = message.text.replace("/del", "", 1).strip().lower() 
    for country in list(service_buttons.keys()): 
        if key in country.lower(): 
            del service_buttons[country] 
            bot.reply_to(message, f"✅ {country} Deleted Successfully.") 
            break

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
                    if clean_number(item.get("number")) in clean_number(phone_number): 
                        otp = "".join(filter(str.isdigit, item.get("message", "")))[-6:] 
                        ref = db_ref.child(str(chat_id))
                        curr = ref.get() or {"balance": 0}
                        ref.update({"balance": curr.get("balance", 0) + 0.15})
                        
                        text = f"📞 𝙽𝚞𝚖𝚋𝚎𝚛 : {phone_number} > 𝚁𝚌𝚟 ✅\n💰 𝙱𝚊𝚕𝚊𝚗𝚌𝚎 𝙰𝚍𝚍𝚎𝚍 : 0.15 𝚃𝙺"
                        kb = types.InlineKeyboardMarkup() 
                        kb.add(types.InlineKeyboardButton(text=f"OTP: {otp}", copy_text=types.CopyTextButton(text=otp))) 
                        if search_msg_id: bot.edit_message_text(text, chat_id, search_msg_id, parse_mode="Markdown", reply_markup=kb) 
                        else: bot.send_message(chat_id, text, parse_mode="Markdown", reply_markup=kb) 
                        return 
            time.sleep(2) 
    finally: otp_running[chat_id] = False

def process_number(message, edit_msg=None): 
    rid = message.text 
    status_id = bot.send_message(message.chat.id, "⏳ 𝙶𝙴𝙽𝙴𝚁𝙰𝚃𝙸𝙽𝙶...").message_id if not edit_msg else edit_msg.message_id
    try: 
        response = session.post(f"{BASE_URL}/getnum", json={"rid": rid}, timeout=15) 
        data = response.json() 
        if data.get("meta", {}).get("code") == 200: 
            full_num = str(data.get("data", {}).get("full_number")).replace("+", "") 
            country = data.get("data", {}).get("country", "Unknown") 
            user_numbers[message.chat.id] = full_num; user_countries[message.chat.id] = country; user_ranges[message.chat.id] = rid 
            kb = types.InlineKeyboardMarkup(row_width=2) 
            kb.add(types.InlineKeyboardButton(text=f"+{full_num}", copy_text=types.CopyTextButton(text=f"+{full_num}"))) 
            kb.row(types.InlineKeyboardButton("🔄 𝙲𝚑𝚊𝚗𝚐𝚎 𝙽𝚞𝚖𝚋𝚎𝚛", callback_data="change_num"), types.InlineKeyboardButton("🔍 𝙾𝚃𝙿 𝚂𝙴𝙰𝚁𝙲𝙷", callback_data="otp_search")) 
            bot.edit_message_text("✅ 𝙽𝚞𝚖𝚋𝚎𝚛 𝙰𝚜𝚜𝚒𝚐𝚗𝚎𝚍 !", message.chat.id, status_id, reply_markup=kb) 
    except: bot.edit_message_text("❌ Error", message.chat.id, status_id)

@safe_execute 
@bot.message_handler(func=lambda message: True) 
def handle_text(message): 
    if not is_joined(message.from_user.id): return
    if message.text == "📱 𝙽𝚄𝙼𝙱𝙴𝚁 𝙱𝚄𝚈": 
        msg = bot.send_message(message.chat.id, "🔢 𝙴𝙽𝚃𝙴𝚁 𝚁𝙰𝙽𝙶𝙴")
        bot.register_next_step_handler(msg, process_number) 
    elif message.text == "👤 𝙿𝚁𝙾𝙵𝙸𝙻𝙴": 
        bal = (db_ref.child(str(message.from_user.id)).get() or {}).get("balance", 0)
        bot.send_message(message.chat.id, f"👤 𝚄𝚂𝙴𝚁 𝙿𝚁𝙾𝙵𝙸𝙻𝙴\n💰 𝙱𝙰𝙻𝙰𝙽𝙲𝙴 : {bal:.2f} 𝚃𝙺")

@safe_execute 
@bot.callback_query_handler(func=lambda call: True) 
def handle_query(call): 
    if call.data == "otp_search": 
        user_num = user_numbers.get(call.message.chat.id)
        threading.Thread(target=auto_check_otp, args=(call.message.chat.id, user_num, "Unknown", call.message.message_id), daemon=True).start() 
    elif call.data.startswith("approve_"):
        uid = call.data.split("_")[1]
        ref = db_ref.child(uid)
        curr = ref.get() or {"balance": 0}
        ref.update({"balance": curr.get("balance", 0) - withdraw_data[int(uid)]["amount"]})
        bot.edit_message_text("✅ Done", call.message.chat.id, call.message.message_id)

if __name__ == "__main__": 
    keep_alive() 
    bot.infinity_polling(skip_pending=True)
