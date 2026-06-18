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

# --- FIREBASE SETUP ---
secret_path = '/etc/secrets/serviceAccountKey.json'
local_path = 'serviceAccountKey.json'
cred_path = secret_path if os.path.exists(secret_path) else local_path

if os.path.exists(cred_path):
    cred = credentials.Certificate(cred_path)
    # আপনার ডাটাবেস URL এখানে বসাতে ভুলবেন না
    firebase_admin.initialize_app(cred, {'databaseURL': 'https://your-database-url.firebaseio.com'})
    ref = db.reference('users')

# --- RENDER KEEP-ALIVE ---
app = Flask('')
@app.route('/')
def home(): return "Bot is Running Live!"
Thread(target=lambda: app.run(host='0.0.0.0', port=8080), daemon=True).start()

# --- CONFIG ---
API_KEY = "MUBTR1MKUBO"
# নতুন টোকেন আপডেট করা হয়েছে
BOT_TOKEN = "8510677584:AAFBV4Jn8OpLOfnUEoQuyiByLQ9pEKOKrRc" 
BASE_URL = "https://api.2oo9.cloud/MXS47FLFX0U/tness/@public/api"
ADMIN_ID = "6136815573"
GROUP_URL = "https://t.me/tem_withh"

bot = telebot.TeleBot(BOT_TOKEN, threaded=True)
session = requests.Session()
session.headers.update({"mauthapi": API_KEY})

# --- FUNCTIONS ---
def update_balance(user_id, amount):
    if 'ref' in globals():
        u = ref.child(str(user_id))
        curr = u.child('balance').get() or 0.0
        u.update({'balance': round(curr + amount, 2)})

# --- COMMANDS & UI ---
@bot.message_handler(commands=['addmoney'])
def add_money(m):
    if str(m.from_user.id) == ADMIN_ID:
        try:
            parts = m.text.split()
            update_balance(parts[1], float(parts[2]))
            bot.reply_to(m, f"✅ User {parts[1]} এ {parts[2]} টাকা যোগ হয়েছে।")
        except: bot.reply_to(m, "⚠️ Format: /addmoney [id] [amount]")

@bot.message_handler(commands=['start'])
def start(m):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("📱 𝙶𝙴𝚃 𝙽𝚄𝙼𝙱𝙴𝚁", "📱 𝙽𝚄𝙼𝙱𝙴𝚁 𝙱𝚄𝚈")
    kb.row("🔐 𝙶𝙴𝚃 2𝙵𝙰 𝙲𝙾𝙳𝙴", "👤 𝙿𝚁𝙾𝙵𝙸𝙻𝙴")
    bot.send_message(m.chat.id, "👋 𝚆𝙴𝙻𝙲𝙾𝙼𝙴 𝚃𝙾 𝚃𝙴𝙰𝙼 𝚆𝙸𝚃𝙷 3.0", reply_markup=kb)

@bot.message_handler(func=lambda m: m.text == "👤 𝙿𝚁𝙾𝙵𝙸𝙻𝙴")
def profile(m):
    bal = 0.0
    if 'ref' in globals():
        bal = ref.child(str(m.from_user.id)).child('balance').get() or 0.0
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("🏦 𝚆𝙸𝚃𝙷𝙳𝚁𝙰𝚆", callback_data="w_start"))
    text = f"👤 𝚄𝚂𝙴𝚁 𝙿𝚁𝙾𝙵𝙸𝙻𝙴\n🆔 : {m.from_user.id}\n💰 𝙱𝙰𝙻𝙰𝙽𝙲𝙴 : {bal} 𝚃𝙺\n✅ 𝚂𝚃𝙰𝚃𝚄𝚂 : 𝙰𝙲𝚃𝙸𝚅𝙴"
    bot.send_message(m.chat.id, text, reply_markup=kb)

@bot.callback_query_handler(func=lambda c: True)
def callback(c):
    if c.data == "w_start":
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton("💳 𝙱𝙺𝙰𝚂𝙷", callback_data="pay_bkash"), 
               types.InlineKeyboardButton("🚀 𝚁𝙾𝙲𝙺𝙴𝚃", callback_data="pay_rocket"))
        kb.add(types.InlineKeyboardButton("❌ 𝙲𝙰𝙽𝙲𝙴𝙻", callback_data="cancel_w"))
        bot.edit_message_text("🏦 𝚂𝙴𝙻𝙴𝙲𝚃 𝙿𝙰𝚈𝙼𝙴𝙽𝚃 𝙼𝙴𝚃𝙷𝙾𝙳", c.message.chat.id, c.message.message_id, reply_markup=kb)
    elif c.data == "cancel_w":
        bot.delete_message(c.message.chat.id, c.message.message_id)

# --- BOT RUNNER ---
if __name__ == "__main__":
    print("Bot Starting...")
    bot.infinity_polling()
