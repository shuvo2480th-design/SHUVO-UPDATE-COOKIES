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

# --- RENDER KEEP-ALIVE SERVER ---
app = Flask(__name__)

@app.route("/")
def home():
    return "Bot is Running Live!"

@app.route("/health")
def health():
    return {"status": "online"}

def run():
    app.run(host="0.0.0.0", port=8080)

def keep_alive():
    Thread(target=run, daemon=True).start()
# -------------------------------

# কনফিগারেশন
API_KEY = "MUBTR1MKUBO"
BOT_TOKEN = "8510677584:AAED9K6-P1gtaNU5Ca8_3k5NpLmJ4ZOpH2s" # নতুন টোকেন
BASE_URL = "https://api.2oo9.cloud/MXS47FLFX0U/tness/@public/api"
HEADERS = {"mauthapi": API_KEY}
ADMIN_ID = "6136815573"
GROUP_URL = "https://t.me/tem_with" 

users = {} 
withdraw_data = {}

session = requests.Session()
session.headers.update(HEADERS)

logging.basicConfig(level=logging.ERROR, format="%(asctime)s - %(levelname)s - %(message)s")

bot = telebot.TeleBot(BOT_TOKEN, threaded=True, num_threads=20)

user_ranges = {}
user_numbers = {}
user_countries = {}
service_buttons = {} 
REQUIRED_CHANNELS = ["@tem_with"] 
otp_running = {}   

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
    kb.add(types.InlineKeyboardButton("📢 Join Channel", url="https://t.me/tem_with"))
    kb.add(types.InlineKeyboardButton("✅ VERIFIED", callback_data="verify_join"))
    return kb

@safe_execute
@bot.message_handler(commands=['start'])
def start(message):
    if not is_joined(message.from_user.id):
        bot.send_message(message.chat.id, "⚠️ To use this bot, you must join our channel: https://t.me/tem_with", reply_markup=join_markup())
        return
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.row(types.KeyboardButton("📱 𝙶𝙴𝚃 𝙽𝚄𝙼𝙱𝙴𝚁"), types.KeyboardButton("📱 𝙽𝚄𝙼𝙱𝙴𝚁 𝙱𝚄𝚈"))
    markup.add(types.KeyboardButton("🔐 𝙶𝙴𝚃 2𝙵𝙰 𝙲𝙾𝙳𝙴"), types.KeyboardButton("👤 𝙿𝚁𝙾𝙵𝙸𝙻𝙴"))
    markup.add(types.KeyboardButton("👑 𝙰𝙳𝙼𝙸𝙽 𝚂𝚄𝙿𝙿𝙾𝚁𝚃"))
    bot.send_message(message.chat.id, "👋𓆩𓆩𝚆𝙴𝙻𝙲𝙾𝙼𝙴 𝚃𝙾 𝙾𝚃𝙿 𝚂𝙴𝚁𝚅𝙸𝙲𝙴𓆪𓆪\n\n🤖 𝚃𝙴𝙰𝙼 𝚆𝙸𝚃𝙷 3.0 𝙽𝚄𝙼𝙱𝙴𝚁 𝙱𝙾𝚃", reply_markup=markup)

@bot.message_handler(commands=['add_balance'])
def add_bal(message):
    if str(message.from_user.id) != ADMIN_ID: return
    try:
        parts = message.text.split()
        uid = parts[1]
        amt = float(parts[2])
        if uid not in users: users[uid] = {"balance": 0}
        users[uid]["balance"] += amt
        bot.reply_to(message, f"✅ User {uid} balance updated by {amt} TK")
    except:
        bot.reply_to(message, "Usage: /add_balance <uid> <amount>")

@bot.message_handler(func=lambda message: message.text == "👤 𝙿𝚁𝙾𝙵𝙸𝙻𝙴")
def show_profile(message):
    uid = str(message.from_user.id)
    bal = users.get(uid, {}).get("balance", 0)
    profile_text = f"👤 𝚄𝚂𝙴𝚁 𝙿𝚁𝙾𝙵𝙸𝙻𝙴\n\n🆔 𝙸𝙳 : {uid}\n💰 𝙱𝙰𝙻𝙰𝙽𝙲𝙴 : {bal:.2f} 𝚃𝙺\n\n✅ 𝚂𝚃𝙰𝚃𝚄𝚂 : 𝙰𝙲𝚃𝙸𝚅𝙴"
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🏦 𝚆𝙸𝚃𝙷𝙳𝚁𝙰𝚆", callback_data="withdraw"))
    bot.send_message(message.chat.id, profile_text, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "withdraw")
def withdraw_menu(call):
    uid = str(call.from_user.id)
    if users.get(uid, {}).get("balance", 0) < 20:
        bot.answer_callback_query(call.id, "❌ Minimum Withdraw 20 TK", show_alert=True)
        return
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(types.InlineKeyboardButton("💳 𝙱𝙺𝙰𝚂𝙷", callback_data="bkash"), types.InlineKeyboardButton("💳 𝚁𝙾𝙲𝙺𝙴𝚃", callback_data="rocket"))
    bot.edit_message_text("🏦 𝚂𝙴𝙻𝙴𝙲𝚃 𝙿𝙰𝚈𝙼𝙴𝙽𝚃 𝙼𝙴𝚃𝙷𝙾𝙳", call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data in ["bkash", "rocket"])
def get_payment_details(call):
    withdraw_data[call.from_user.id] = {"method": call.data}
    msg = bot.send_message(call.message.chat.id, "📱 Enter your number:")
    bot.register_next_step_handler(msg, lambda m: get_amount(m, call.data))

def get_amount(message, method):
    withdraw_data[message.from_user.id]["number"] = message.text
    msg = bot.send_message(message.chat.id, "💰 Enter amount (Min 20 TK):")
    bot.register_next_step_handler(msg, finalize_withdraw)

def finalize_withdraw(message):
    try:
        amt = int(message.text)
        uid = str(message.from_user.id)
        if amt < 20:
            bot.send_message(message.chat.id, "❌ Min 20 TK")
            return
        users[uid]["balance"] -= amt
        bot.send_message(message.chat.id, "✅ Request sent to Admin!")
        bot.send_message(ADMIN_ID, f"💸 New Request\nID: {uid}\nAmount: {amt} TK\nMethod: {withdraw_data[uid]['method']}")
    except:
        bot.send_message(message.chat.id, "❌ Invalid input.")

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

@safe_execute
@bot.message_handler(func=lambda message: True)
def handle_text(message):
    if not is_joined(message.from_user.id):
        bot.send_message(message.chat.id, "⚠️ To use this bot, you must join our channel: https://t.me/tem_with", reply_markup=join_markup())
        return
    if message.text == "📱 𝙽𝚄𝙼𝙱𝙴𝚁 𝙱𝚄𝚈":
        msg = bot.send_message(message.chat.id, "⚙️ 𝙿𝙻𝙴𝙰𝚂𝙴 𝙴𝙽𝚃𝙴𝚁 𝚈𝙾𝚄𝚁 𝚁𝙰𝙽𝙶𝙴\n\n🔢 𝙴𝚡𝚊𝚖𝚙𝚕𝚎 : `2245564`", parse_mode="Markdown")
        bot.register_next_step_handler(msg, process_number)
    elif message.text == "📱 𝙶𝙴𝚃 𝙽𝚄𝙼𝙱𝙴𝚁":
        kb = types.InlineKeyboardMarkup(row_width=1)
        for country in service_buttons: kb.add(types.InlineKeyboardButton(text=f"{get_flag(country)} {country}", callback_data=f"service_{country}"))
        bot.send_message(message.chat.id, "🟢 𝘾𝙝𝙤𝙤𝙨𝙚 𝙎𝙚𝙧𝙫𝙞𝙘𝙚 🟢", reply_markup=kb)
    elif message.text == "🔐 𝙶𝙴𝚃 2𝙵𝙰 𝙲𝙾𝙳𝙴":
        msg = bot.send_message(message.chat.id, "🔐 𝙿𝙻𝙴𝙰𝚂𝙴 𝙴𝙽𝚃𝙴𝚁 𝚈𝙾𝚄𝚁 𝟸𝙵𝙰 𝙺𝙴𝚈")
        bot.register_next_step_handler(msg, process_2fa)
    elif message.text == "👑 𝙰𝙳𝙼𝙸𝙽 𝚂𝚄𝙿𝙿𝙾𝚁𝚃":
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton("📩 এডমিনকে মেসেজ দিন", url=f"tg://user?id={ADMIN_ID}"))
        bot.send_message(message.chat.id, "💬 যেকোনো সমস্যার জন্য এডমিনকে মেসেজ দিন।", reply_markup=kb)

def process_2fa(message):
    code = str(random.randint(100000, 999999))
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton(text=f"{code}", copy_text=types.CopyTextButton(text=code)))
    bot.send_message(message.chat.id, f"🔐 𝚈𝙾𝚄𝚁 𝟸𝙵𝙰 𝙲𝙾𝙳𝙴 ✅\n\n`{code}`", parse_mode="Markdown", reply_markup=kb)

def auto_check_otp(chat_id, phone_number, country, search_msg_id=None):
    if otp_running.get(chat_id): return
    otp_running[chat_id] = True
    uid = str(chat_id)
    if uid not in users: users[uid] = {"balance": 0}
    users[uid]["balance"] += 0.15
    
    start_time = time.time()
    try:
        while time.time() - start_time < 30:
            response = session.get(f"{BASE_URL}/success-otp", timeout=15)
            if response.status_code == 200:
                data = response.json()
                if data.get("meta", {}).get("code") == 200:
                    for item in data.get("data", {}).get("otps", []):
                        if clean_number(item.get("number")) in clean_number(phone_number):
                            otp = "".join(filter(str.isdigit, item.get("message", "")))[-6:]
                            text = f"✅ OTP RECEIVED\n\n🟢 Country : {get_flag(country)} {country}\n📞 Number : +{phone_number}\n\n🔑 OTP : `{otp}`\n💰 𝙴𝚊𝚛𝚗 : 0.15 𝚃𝙺"
                            kb = types.InlineKeyboardMarkup()
                            kb.add(types.InlineKeyboardButton(text=otp, copy_text=types.CopyTextButton(text=otp)))
                            if search_msg_id: bot.edit_message_text(text, chat_id, search_msg_id, parse_mode="Markdown", reply_markup=kb)
                            else: bot.send_message(chat_id, text, parse_mode="Markdown", reply_markup=kb)
                            return
            time.sleep(3)
    finally:
        otp_running[chat_id] = False

def process_number(message, edit_msg=None):
    rid = message.text
    status_id = edit_msg.message_id if edit_msg else bot.send_message(message.chat.id, "⏳ 𝙿𝙻𝙴𝙰𝚂𝙴 𝚆𝙰𝙸𝚃...").message_id
    try:
        response = session.post(f"{BASE_URL}/getnum", json={"rid": rid}, timeout=15, verify=False)
        data = response.json()
        if data.get("meta", {}).get("code") == 200:
            full_num = str(data.get("data", {}).get("full_number")).replace("+", "")
            country = data.get("data", {}).get("country", "Unknown")
            user_numbers[message.chat.id] = full_num
            user_countries[message.chat.id] = country
            user_ranges[message.chat.id] = rid
            kb = types.InlineKeyboardMarkup(row_width=2)
            kb.add(types.InlineKeyboardButton(text=f"+{full_num}", copy_text=types.CopyTextButton(text=f"+{full_num}")))
            kb.row(types.InlineKeyboardButton("🔄 𝙲𝚑𝚊𝚗𝚐𝚎 𝙽𝚞𝚖𝚋𝚎𝚛", callback_data="change_num"), types.InlineKeyboardButton("🔍 𝙾𝚃𝙿 𝚂𝙴𝙰𝚁𝙲𝙷", callback_data="otp_search"))
            bot.edit_message_text(f"✅ Number Assigned!\n📞 {full_num}", message.chat.id, status_id, reply_markup=kb)
        else: bot.edit_message_text("❌ নাম্বার পাওয়া যায়নি!", message.chat.id, status_id)
    except Exception as e: bot.edit_message_text(f"❌ ত্রুটি: {e}", message.chat.id, status_id)

@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    if call.data == "verify_join":
        if is_joined(call.from_user.id): bot.answer_callback_query(call.id, "✅ You are verified!"); start(call.message)
        else: bot.answer_callback_query(call.id, "❌ Still not joined!")
    elif call.data == "otp_search":
        threading.Thread(target=auto_check_otp, args=(call.message.chat.id, user_numbers.get(call.message.chat.id), user_countries.get(call.message.chat.id), call.message.message_id), daemon=True).start()
    elif call.data.startswith("service_"):
        country = call.data.replace("service_", "", 1)
        fake_msg = type("obj", (object,), {"chat": call.message.chat, "text": service_buttons.get(country)})()
        process_number(fake_msg)

if __name__ == "__main__":
    keep_alive()
    bot.remove_webhook()
    print("Bot is Starting...")
    bot.infinity_polling(timeout=30, long_polling_timeout=30, skip_pending=True)
