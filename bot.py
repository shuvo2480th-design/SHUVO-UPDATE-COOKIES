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

# --- FIREBASE SETUP ---
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

user_ranges, user_numbers, user_countries = {}, {}, {}
service_buttons = {}
REQUIRED_CHANNELS = ["@range_channele", "@tem_withh"]
otp_running = {}

# --- HELPER FUNCTIONS ---
def update_balance(user_id, amount):
    user_ref = ref.child(str(user_id))
    current = user_ref.child('balance').get() or 0.0
    user_ref.update({'balance': round(current + amount, 2)})

# --- এডমিন কমান্ড: টাকা যোগ করার জন্য ---
@bot.message_handler(commands=['addmoney'])
def add_money_admin(message):
    if str(message.from_user.id) != ADMIN_ID: return
    try:
        parts = message.text.split()
        target_id = parts[1]
        amount = float(parts[2])
        update_balance(target_id, amount)
        bot.reply_to(message, f"✅ User {target_id} এর ব্যালেন্সে {amount} টাকা যোগ করা হয়েছে।")
    except:
        bot.reply_to(message, "⚠️ সঠিক ফরম্যাট: /addmoney [user_id] [amount]")

# --- বাকি সব আগের ফাংশন ---
# ... (এখানে আপনার আগের সব ফাংশন যেমন: is_joined, start, handle_text ইত্যাদি থাকবে) ...

@bot.message_handler(func=lambda message: message.text == "👤 𝙿𝚁𝙾𝙵𝙸𝙻𝙴")
def user_profile(message):
    bal = ref.child(str(message.from_user.id)).child('balance').get() or 0.0
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("🏦 𝚆𝙸𝚃𝙷𝙳𝚁𝙰𝚆", callback_data="w_start"))
    text = f"👤 𝚄𝚂𝙴𝚁 𝙿𝚁𝙾𝙵𝙸𝙻𝙴\n\n🆔 𝙸𝙳 : {message.from_user.id}\n💰 𝙱𝙰𝙻𝙰𝙽𝙲𝙴 : {bal:.2f} 𝚃𝙺\n\n✅ 𝚂𝚃𝙰𝚃𝚄𝚂 : 𝙰𝙲𝚃𝙸𝚅𝙴"
    bot.send_message(message.chat.id, text, reply_markup=kb)

# --- অটো ওটিপি ব্যালেন্স এড ---
def auto_check_otp(chat_id, phone_number, country, search_msg_id=None):
    # (পূর্বের লজিক)
    update_balance(chat_id, 0.15) 
    # (বাকি লজিক)
    pass

def run_bot():
    while True:
        try:
            bot.infinity_polling(timeout=60, long_polling_timeout=60, skip_pending=True)
        except Exception:
            logging.error(traceback.format_exc())
            time.sleep(5)

if __name__ == "__main__":
    run_bot()
