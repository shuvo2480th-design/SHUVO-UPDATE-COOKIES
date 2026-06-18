# -*- coding: utf-8 -*-
import telebot
import requests
import json
import pycountry
import threading
import time
import re
import os
import logging
import traceback
from flask import Flask
from threading import Thread
from telebot import types
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

# --- RENDER KEEP-ALIVE SERVER ---
app = Flask('')
@app.route('/')
def home():
    return "Bot is Running Live!"

def run_flask():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run_flask)
    t.start()
# -------------------------------

# কনফিগারেশন
API_KEY = "MUBTR1MKUBO"
BOT_TOKEN = "8510677584:AAFBV4Jn8OpLOfnUEoQuyiByLQ9pEKOKrRc"
BASE_URL = "https://api.2oo9.cloud/MXS47FLFX0U/tness/@public/api"
HEADERS = {"mauthapi": API_KEY}
ADMIN_ID = "6136815573"
GROUP_URL = "https://t.me/tem_withh"

# ডাটাবেস ও ইউজার ব্যালেন্স
users = {} # লোকাল স্টোরেজ
withdraw_data = {}

# ===================== STABLE SESSION =====================
session = requests.Session()
session.headers.update(HEADERS)

logging.basicConfig(level=logging.ERROR, format="%(asctime)s - %(levelname)s - %(message)s")

bot = telebot.TeleBot(BOT_TOKEN, threaded=True, num_threads=20)

user_ranges = {}
user_numbers = {}
user_countries = {}
service_buttons = {}  
REQUIRED_CHANNELS = ["@range_channele", "@tem_withh"]
otp_running = {}   

# ===================== GLOBAL ERROR PROTECTION =====================
def safe_execute(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception:
            logging.error(traceback.format_exc())
    return wrapper

def clean_number(num):
    return "".join(filter(str.isdigit, str(num)))

def get_flag(country_name):
    try:
        country = pycountry.countries.lookup(country_name)
        code = country.alpha_2
        return "".join(chr(ord(c) + 127397) for c in code.upper())
    except:
        return "🌍"

def is_joined(user_id):
    try:
        for channel in REQUIRED_CHANNELS:
            member = bot.get_chat_member(channel, user_id)
            if member.status not in ["member", "administrator", "creator"]:
                return False
        return True
    except:
        return False

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
    
    welcome_text = (
        "👋𓆩𓆩𝚆𝙴𝙻𝙲𝙾𝙼𝙴 𝚃𝙾 𝙾𝚃𝙿 𝚂𝙴𝚁𝚅𝙸𝙲𝙴𓆪𓆪\n"
        "﹌﹌﹌﹌﹌﹌﹌﹌﹌﹌﹌﹌﹌﹌﹌﹌﹌﹌﹌\n\n"
        "🤖 𝚆𝙴𝙻𝙲𝙾𝙼𝙴 𝚃𝙾 𝚃𝙴𝙰𝙼 𝚆𝙸𝚃𝙷 3.0 𝙽𝚄𝙼𝙱𝙴𝚁 𝙱𝙾𝚃\n\n"
        "﹌﹌﹌﹌﹌﹌﹌﹌﹌﹌﹌﹌﹌﹌﹌﹌﹌﹌﹌\n\n"
        "♾️ 𝙿𝙾𝚆𝙴𝚁𝙴𝙳 𝙱𝚈 Shuvoᯓᡣ𐭩"
    )
    bot.send_message(message.chat.id, welcome_text, reply_markup=markup)

# --- নতুন প্রোফাইল হ্যান্ডলার ---
@bot.message_handler(func=lambda message: message.text == "👤 𝙿𝚁𝙾𝙵𝙸𝙻𝙴")
def show_profile(message):
    user_id = str(message.from_user.id)
    balance = users.get(user_id, {}).get("balance", 0)
    profile_text = f"👤 𝚄𝚂𝙴𝚁 𝙿𝚁𝙾𝙵𝙸𝙻𝙴\n\n🆔 𝙸𝙳 : {message.from_user.id}\n💰 𝙱𝙰𝙻𝙰𝙽𝙲𝙴 : {balance:.2f}$\n\n✅ 𝚂𝚃𝙰𝚃𝚄𝚂 : 𝙰𝙲𝚃𝙸𝚅𝙴"
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(types.InlineKeyboardButton("🏦 𝚆𝙸𝚃𝙷𝙳𝚁𝙰𝚆", callback_data="withdraw"))
    bot.send_message(message.chat.id, profile_text, reply_markup=markup)

# --- WITHDRAW সিস্টেম ---
@bot.callback_query_handler(func=lambda call: call.data == "withdraw")
def withdraw_menu(call):
    user_id = str(call.from_user.id)
    balance = users.get(user_id, {}).get("balance", 0)
    if balance < 20:
        bot.answer_callback_query(call.id, "❌ Minimum Withdraw 20 TK Required!", show_alert=True)
        return
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(types.InlineKeyboardButton("💳 𝙱𝙺𝙰𝚂𝙷", callback_data="bkash"), types.InlineKeyboardButton("💳 𝚁𝙾𝙲𝙺𝙴𝚃", callback_data="rocket"))
    markup.add(types.InlineKeyboardButton("❌ 𝙲𝙰𝙽𝙲𝙴𝙻", callback_data="withdraw_cancel"))
    bot.edit_message_text("🏦 𝚂𝙴𝙻𝙴𝙲𝚃 𝙿𝙰𝚈𝙼𝙴𝙽𝚃 𝙼𝙴𝚃𝙷𝙾𝙳", call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "withdraw_cancel")
def cancel_withdraw(call):
    bot.edit_message_text("❌ 𝚆𝙸𝚃𝙷𝙳𝚁𝙰𝚆 𝙲𝙰𝙽𝙲𝙴𝙻𝙻𝙴𝙳", call.message.chat.id, call.message.message_id)

@bot.callback_query_handler(func=lambda call: call.data in ["bkash", "rocket"])
def payment_method(call):
    withdraw_data[call.from_user.id] = {"method": call.data.capitalize()}
    msg = bot.send_message(call.message.chat.id, f"📱 𝙴𝙽𝚃𝙴𝚁 𝚈𝙾𝚄𝚁 {call.data.upper()} 𝙽𝚄𝙼𝙱𝙴𝚁")
    bot.register_next_step_handler(msg, get_number)

def get_number(message):
    withdraw_data[message.from_user.id]["number"] = message.text
    msg = bot.send_message(message.chat.id, "💰 𝙴𝙽𝚃𝙴𝚁 𝙰𝙼𝙾𝚄𝙽𝚃\n\n⚠️ 𝙼𝙸𝙽𝙸𝙼𝚄𝙼 : 20 𝚃𝙺")
    bot.register_next_step_handler(msg, get_amount)

def get_amount(message):
    try:
        amount = int(message.text)
        if amount < 20:
            bot.send_message(message.chat.id, "❌ 𝙼𝙸𝙽𝙸𝙼𝚄𝙼 𝚆𝙸𝚃𝙷𝙳𝚁𝙰𝚆 : 20 𝚃𝙺")
            return
        
        user_id = message.from_user.id
        withdraw_data[user_id]["amount"] = amount
        
        # Admin request logic
        admin_text = f"💸 𝙽𝙴𝚆 𝙿𝙰𝚈𝙼𝙴𝙽𝚃 𝚁𝙴𝚀𝚄𝙴𝚂𝚃\n\n👤 𝙽𝙰𝙼𝙴 : {message.from_user.first_name}\n🆔 𝙸𝙳 : {user_id}\n💰 𝙱𝙰𝙻𝙰𝙽𝙲𝙴 : {amount} 𝚃𝙺\n📱 {withdraw_data[user_id]['method']} : {withdraw_data[user_id]['number']}"
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("❌ 𝚁𝙴𝙹𝙴𝙲𝚃", callback_data=f"reject_{user_id}"), types.InlineKeyboardButton("✅ 𝙰𝙿𝙿𝚁𝙾𝚅𝙴", callback_data=f"approve_{user_id}"))
        bot.send_message(ADMIN_ID, admin_text, reply_markup=markup)
        bot.send_message(message.chat.id, "✅ 𝚆𝙸𝚃𝙷𝙳𝚁𝙰𝚆 𝚂𝚄𝙲𝙲𝙴𝚂𝚂𝙵𝚄𝙻\n⏳ 𝚆𝙰𝙸𝚃𝙸𝙽𝙶 𝙵𝙾𝚁 𝙰𝙳𝙼𝙸𝙽 𝙰𝙿𝙿𝚁𝙾𝚅𝙰𝙻")
    except:
        bot.send_message(message.chat.id, "❌ Invalid input.")

# --- এডমিন এপ্রুভ/রিজেক্ট ---
@bot.callback_query_handler(func=lambda call: call.data.startswith(("approve_", "reject_")))
def handle_admin_decision(call):
    action, user_id = call.data.split("_")
    if action == "approve":
        bot.send_message(user_id, "✅ 𝚆𝙸𝚃𝙷𝙳𝚁𝙰𝚆 𝚂𝚄𝙲𝙲𝙴𝚂𝚂!")
        bot.answer_callback_query(call.id, "Payment Approved")
    else:
        bot.send_message(user_id, "❌ 𝙰𝙳𝙼𝙸𝙽 𝚁𝙴𝙹𝙴𝙲𝚃𝙴𝙳 𝚈𝙾𝚄𝚁 𝙿𝙰𝚈𝙼𝙴𝙽𝚃")
        bot.answer_callback_query(call.id, "Payment Rejected")
    bot.delete_message(call.message.chat.id, call.message.message_id)

# --- OTP রিসিভ লজিক (আপনার আগের অংশ) ---
def auto_check_otp(chat_id, phone_number, country, search_msg_id=None):
    if otp_running.get(chat_id): return
    otp_running[chat_id] = True
    # OTP পেলে ব্যালেন্স আপডেট
    user_id = str(chat_id)
    if user_id not in users: users[user_id] = {"balance": 0}
    users[user_id]["balance"] += 0.15
    
    # বাকি আগের OTP লজিক...
    otp_running[chat_id] = False

# [বাকি ফাংশনগুলো আগের মতোই থাকবে]
def run_bot():
    keep_alive()
    while True:
        try:
            print("Bot Started...")
            bot.infinity_polling(timeout=60, long_polling_timeout=60, skip_pending=True, logger_level=logging.ERROR)
        except:
            time.sleep(5)

if __name__ == "__main__":
    run_bot()
