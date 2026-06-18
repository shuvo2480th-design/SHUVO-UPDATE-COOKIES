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
import firebase_admin
from firebase_admin import credentials, db
from flask import Flask
from threading import Thread
from telebot import types
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

# --- FIREBASE SETUP (আপনার ডিবি লিংক এখানে বসান) ---
cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred, {'databaseURL': 'YOUR_FIREBASE_DATABASE_URL'})
ref = db.reference('users')

# --- RENDER KEEP-ALIVE SERVER ---
app = Flask('')
@app.route('/')
def home(): return "Bot is Running Live!"
def run_flask(): app.run(host='0.0.0.0', port=8080)
def keep_alive():
    t = Thread(target=run_flask)
    t.start()
keep_alive()

# --- কনফিগারেশন ---
API_KEY = "MUBTR1MKUBO"
BOT_TOKEN = "8510677584:AAG-y26-o5m7hUit-mVA1OHAKgLtcTHaxbI"
BASE_URL = "https://api.2oo9.cloud/MXS47FLFX0U/tness/@public/api"
HEADERS = {"mauthapi": API_KEY}
ADMIN_ID = "6136815573"
GROUP_URL = "https://t.me/tem_withh"

# --- STABLE SESSION ---
session = requests.Session()
session.headers.update(HEADERS)

import logging
import traceback

logging.basicConfig(level=logging.ERROR, format="%(asctime)s - %(levelname)s - %(message)s")

bot = telebot.TeleBot(BOT_TOKEN, threaded=True, num_threads=20)

user_ranges = {}
user_numbers = {}
user_countries = {}
service_buttons = {}
REQUIRED_CHANNELS = ["@range_channele", "@tem_withh"]
otp_running = {}

# --- HELPER FUNCTIONS ---
def update_balance(user_id, amount):
    user_ref = ref.child(str(user_id))
    current = user_ref.child('balance').get() or 0.0
    user_ref.update({'balance': round(current + amount, 2)})

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
    if not is_joined(message.from_user.id):
        bot.send_message(message.chat.id, "⚠️ বট ব্যবহার করার আগে নিচের দুইটি চ্যানেলে Join করুন এবং তারপর VERIFIED বাটনে চাপুন।", reply_markup=join_markup())
        return
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.row(types.KeyboardButton("📱 𝙶𝙴𝚃 𝙽𝚄𝙼𝙱𝙴𝚁"), types.KeyboardButton("📱 𝙽𝚄𝙼𝙱𝙴𝚁 𝙱𝚄𝚈"))
    markup.add(types.KeyboardButton("🔐 𝙶𝙴𝚃 2𝙵𝙰 𝙲𝙾𝙳𝙴"), types.KeyboardButton("👤 𝙿𝚁𝙾𝙵𝙸𝙻𝙴"))
    markup.add(types.KeyboardButton("👑 𝙰𝙳𝙼𝙸𝙽 𝚂𝚄𝙿𝙿𝙾𝚁𝚃"))
    bot.send_message(message.chat.id, "👋𓆩𓆩𝚆𝙴𝙻𝙲𝙾𝙼𝙴 𝚃𝙾 𝙾𝚃𝙿 𝚂𝙴𝚁𝚅𝙸𝙲𝙴𓆪𓆪\n\n🤖 𝚃𝙴𝙰𝙼 𝚆𝙸𝚃𝙷 3.0 𝙽𝚄𝙼𝙱𝙴𝚁 𝙱𝙾𝚃", reply_markup=markup)

# --- নতুন প্রোফাইল ও উইথড্রল বাটন ---
@bot.message_handler(func=lambda message: message.text == "👤 𝙿𝚁𝙾𝙵𝙸𝙻𝙴")
def user_profile(message):
    bal = ref.child(str(message.from_user.id)).child('balance').get() or 0.0
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("🏦 𝚆𝙸𝚃𝙷𝙳𝚁𝙰𝚆", callback_data="w_start"))
    text = f"👤 𝚄𝚂𝙴𝚁 𝙿𝚁𝙾𝙵𝙸𝙻𝙴\n\n🆔 𝙸𝙳 : {message.from_user.id}\n💰 𝙱𝙰𝙻𝙰𝙽𝙲𝙴 : {bal:.2f}$\n\n✅ 𝚂𝚃𝙰𝚃𝚄𝚂 : 𝙰𝙲𝚃𝙸𝚅𝙴"
    bot.send_message(message.chat.id, text, reply_markup=kb)

# --- উইথড্রল ও অ্যাডমিন লজিক ---
@bot.callback_query_handler(func=lambda call: call.data in ["w_start", "pay_bkash", "pay_rocket", "cancel_w"])
def withdraw_handler(call):
    if call.data == "w_start":
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton("💳 𝙱𝙺𝙰𝚂𝙷", callback_data="pay_bkash"), types.InlineKeyboardButton("🚀 𝚁𝙾𝙲𝙺𝙴𝚃", callback_data="pay_rocket"))
        kb.add(types.InlineKeyboardButton("❌ 𝙲𝙰𝙽𝙲𝙴𝙻", callback_data="cancel_w"))
        bot.edit_message_text("🏦 𝚂𝙴𝙻𝙴𝙲𝚃 𝙿𝙰𝚈𝙼𝙴𝙽𝚃 𝙼𝙴𝚃𝙷𝙾𝙳", call.message.chat.id, call.message.message_id, reply_markup=kb)
    elif call.data == "cancel_w":
        bot.delete_message(call.message.chat.id, call.message.message_id)

# --- OTP লজিক (আপডেট করা) ---
def auto_check_otp(chat_id, phone_number, country, search_msg_id=None):
    if otp_running.get(chat_id): return
    otp_running[chat_id] = True
    start_time = time.time()
    try:
        while time.time() - start_time < 15:
            response = session.get(f"{BASE_URL}/success-otp", timeout=10)
            data = response.json()
            if data.get("meta", {}).get("code") == 200:
                for item in data.get("data", {}).get("otps", []):
                    if clean_number(item.get("number")) in clean_number(phone_number):
                        otp = "".join(filter(str.isdigit, item.get("message", "")))[-6:]
                        update_balance(chat_id, 0.15) # ব্যালেন্স আপডেট
                        text = f"✅ 𝙾𝚃𝙿 𝚁𝙴𝙲𝙴𝙸𝚅𝙴𝙳\n\n🟢 𝙲𝚘𝚞𝚗𝚝𝚛𝚢 : {get_flag(country)} {country}\n📞 𝙽𝚞𝚖𝚋𝚎𝚛 : +{phone_number}\n\n💰 𝙴𝚊𝚛𝚗 : 0.15 𝚃𝙺\n\n🔑 𝙾𝚃𝙿 : {otp}"
                        kb = types.InlineKeyboardMarkup()
                        kb.add(types.InlineKeyboardButton(text=otp, copy_text=types.CopyTextButton(text=otp)))
                        if search_msg_id: bot.edit_message_text(text, chat_id, search_msg_id, parse_mode="Markdown", reply_markup=kb)
                        return
            time.sleep(2)
    finally:
        otp_running[chat_id] = False

# (বাকি সব ফাংশন যেমন handle_text, process_number, handle_query আগের মতোই অপরিবর্তিত থাকবে)

def run_bot():
    while True:
        try:
            bot.infinity_polling(timeout=60, long_polling_timeout=60, skip_pending=True)
        except Exception:
            logging.error(traceback.format_exc())
            time.sleep(5)

if __name__ == "__main__":
    run_bot()