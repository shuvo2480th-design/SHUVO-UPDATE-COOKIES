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

# --- ржХржиржлрж┐ржЧрж╛рж░рзЗрж╢ржи ---
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

# Firebase рж╕рж╛рж░рзНржнрж┐рж╕ рж▓рзЛржб ржУ рж╕рзЗржн
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
service_buttons = load_services_from_firebase()  # Firebase ржерзЗржХрзЗ рж▓рзЛржб рж╣ржмрзЗ
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
    except: return "ЁЯМН"

def is_joined(user_id): 
    try: 
        for channel in REQUIRED_CHANNELS: 
            member = bot.get_chat_member(channel, user_id) 
            if member.status not in ["member", "administrator", "creator"]: return False 
        return True 
    except: return False

def join_markup(): 
    kb = types.InlineKeyboardMarkup(row_width=1) 
    kb.add(types.InlineKeyboardButton("ЁЯУв Join Channel 1", url="https://t.me/range_channele")) 
    kb.add(types.InlineKeyboardButton("ЁЯУв Join Channel 2", url="https://t.me/tem_withh")) 
    kb.add(types.InlineKeyboardButton("тЬЕ VERIFIED", callback_data="verify_join")) 
    return kb

@safe_execute 
@bot.message_handler(commands=['start']) 
def start(message): 
    if str(message.from_user.id) not in users: users[str(message.from_user.id)] = {"balance": 0}
        
    if not is_joined(message.from_user.id): 
        bot.send_message(message.chat.id, "тЪая╕П ржмржЯ ржмрзНржпржмрж╣рж╛рж░ ржХрж░рж╛рж░ ржЖржЧрзЗ ржирж┐ржЪрзЗрж░ ржжрзБржЗржЯрж┐ ржЪрзНржпрж╛ржирзЗрж▓рзЗ Join ржХрж░рзБржи ржПржмржВ рждрж╛рж░ржкрж░ VERIFIED ржмрж╛ржЯржирзЗ ржЪрж╛ржкрзБржиред", reply_markup=join_markup()) 
        return 
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2) 
    markup.row(types.KeyboardButton("ЁЯУ▒ ЁЭЩ╢ЁЭЩ┤ЁЭЪГ ЁЭЩ╜ЁЭЪДЁЭЩ╝ЁЭЩ▒ЁЭЩ┤ЁЭЪБ"), types.KeyboardButton("ЁЯУ▒ ЁЭЩ╜ЁЭЪДЁЭЩ╝ЁЭЩ▒ЁЭЩ┤ЁЭЪБ ЁЭЩ▒ЁЭЪДЁЭЪИ")) 
    markup.add(types.KeyboardButton("ЁЯФР ЁЭЩ╢ЁЭЩ┤ЁЭЪГ 2ЁЭЩ╡ЁЭЩ░ ЁЭЩ▓ЁЭЩ╛ЁЭЩ│ЁЭЩ┤"), types.KeyboardButton("ЁЯСС ЁЭЩ░ЁЭЩ│ЁЭЩ╝ЁЭЩ╕ЁЭЩ╜ ЁЭЪВЁЭЪДЁЭЩ┐ЁЭЩ┐ЁЭЩ╛ЁЭЪБЁЭЪГ"), types.KeyboardButton("ЁЯСд ЁЭЩ┐ЁЭЪБЁЭЩ╛ЁЭЩ╡ЁЭЩ╕ЁЭЩ╗ЁЭЩ┤")) 
    
    welcome_text = (
        "ЁЯСЛЁУЖйЁУЖйЁЭЪЖЁЭЩ┤ЁЭЩ╗ЁЭЩ▓ЁЭЩ╛ЁЭЩ╝ЁЭЩ┤ ЁЭЪГЁЭЩ╛ ЁЭЩ╛ЁЭЪГЁЭЩ┐ ЁЭЪВЁЭЩ┤ЁЭЪБЁЭЪЕЁЭЪТЁЭЩ▓ЁЭЩ┤ЁУЖкЁУЖк\n"
        "я╣Мя╣Мя╣Мя╣Мя╣Мя╣Мя╣Мя╣Мя╣Мя╣Мя╣Мя╣Мя╣Мя╣Мя╣М\n\n"
        "ЁЯдЦ ЁЭЪЖЁЭЩ┤ЁЭЩ╗ЁЭЩ▓ЁЭЩ╛ЁЭЩ╝ЁЭЩ┤ ЁЭЪГЁЭЩ╛ ЁЭЪГЁЭЩ┤ЁЭЩ░ЁЭЩ╝ ЁЭЪЖЁЭЩ╕ЁЭЪГЁЭЩ╖ 3.0 ЁЭЩ╜ЁЭЪДЁЭЩ╝ЁЭЩ▒ЁЭЩ┤ЁЭЪБ ЁЭЩ▒ЁЭЩ╛ЁЭЪГ\n\n"
        "я╣Мя╣Мя╣Мя╣Мя╣Мя╣Мя╣Мя╣Мя╣Мя╣Мя╣Мя╣Мя╣Мя╣Мя╣М\n\n"
        "тЩ╛я╕П ЁЭЩ┐ЁЭЩ╛ЁЭЪЖЁЭЩ┤ЁЭЪБЁЭЩ┤ЁЭЩ│ ЁЭЩ▒ЁЭЪИ ShuvoспУсбгЁРнй"
    )
    bot.send_message(message.chat.id, welcome_text, reply_markup=markup)

@bot.message_handler(commands=['user'])
def count_users(message):
    if str(message.from_user.id) == ADMIN_ID:
        bot.reply_to(message, f"ЁЯСе ржорзЛржЯ ржЗржЙржЬрж╛рж░ рж╕ржВржЦрзНржпрж╛: {len(users)}")

@bot.message_handler(commands=['send'])
def broadcast(message):
    if str(message.from_user.id) == ADMIN_ID:
        text = message.text.replace("/send", "", 1).strip()
        if not text:
            bot.reply_to(message, "тЪая╕П ржХрж┐ржЫрзБ рж▓рж┐ржЦрзБржиред ржпрзЗржоржи: /send рж╣рзНржпрж╛рж▓рзЛ!")
            return
        count = 0
        for uid in users:
            try:
                bot.send_message(uid, text)
                count += 1
            except: pass
        bot.reply_to(message, f"тЬЕ {count} ржЬржи ржЗржЙржЬрж╛рж░ржХрзЗ ржорзЗрж╕рзЗржЬ ржкрж╛ржарж╛ржирзЛ рж╣рзЯрзЗржЫрзЗред")

@bot.message_handler(commands=['add']) 
def add_service(message): 
    if str(message.from_user.id) != ADMIN_ID: return 
    text = message.text.replace("/add", "", 1).strip() 
    if ":" not in text: return 
    country, rid = text.split(":", 1) 
    country, rid = country.strip(), rid.strip()
    service_buttons[country] = rid
    save_service_to_firebase(country, rid)
    bot.reply_to(message, f"тЬЕ Added Successfully\nЁЯМН Country : {country}\nЁЯФв Range : {rid}")

@bot.message_handler(commands=['del']) 
def del_service(message): 
    if str(message.from_user.id) != ADMIN_ID: return 
    key = message.text.replace("/del", "", 1).strip().lower() 
    for country in list(service_buttons.keys()): 
        if key in country.lower(): 
            del service_buttons[country] 
            session.delete(f"{FIREBASE_URL}/services/{country}.json")
            bot.reply_to(message, f"тЬЕ {country} Deleted Successfully.") 
            break

@bot.message_handler(commands=['addmoney']) 
def add_money_by_admin(message): 
    if str(message.from_user.id) != ADMIN_ID: return 
    parts = message.text.split()
    if len(parts) != 3:
        bot.reply_to(message, "тЪая╕П ржнрзБрж▓ ржлрж░ржорзНржпрж╛ржЯ! рж╕ржарж┐ржХ ржирж┐рзЯржо:\n/addmoney [user_id] [amount]")
        return
    uid = parts[1]
    amount = float(parts[2])
    new_bal = update_firebase_balance(uid, amount)
    bot.reply_to(message, f"тЬЕ рж╕ржлрж▓ржнрж╛ржмрзЗ ржмрзНржпрж╛рж▓рзЗржирзНрж╕ ржЖржкржбрзЗржЯ рж╣рзЯрзЗржЫрзЗ!\nЁЯСд ржЗржЙржЬрж╛рж░ ID: {uid}\nЁЯТ░ ржирждрзБржи ржмрзНржпрж╛рж▓рзЗржирзНрж╕: {new_bal} ЁЭЪГЁЭЩ║")

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
                            "тХФтХРтХРтХРтХРтХРтХРтХРтХРтХРтХРтХРтХРтХРтХРтХРтХРтХРтХРтХРтХРтХЧ\n"
                            f"    тЮд {phone_number} тЮд ЁЭЪБЁЭЩ▓ЁЭЪЕЁЭЩ┤ЁЭЩ│ тЬЕ\n"
                            "тХЪтХРтХРтХРтХРтХРтХРтХРтХРтХРтХРтХРтХРтХРтХРтХРтХРтХРтХРтХРтХРтХЭ\n"
                            "ЁЯТ░ ЁЭЩ▒ЁЭЪКЁЭЪХЁЭЪКЁЭЪЧЁЭЪМЁЭЪО ЁЭЩ░ЁЭЪНЁЭЪНЁЭЪОЁЭЪН: +0.15 ЁЭЪГЁЭЩ║  \n"
                            f"ЁЯПж ЁЭЪГЁЭЪШЁЭЪЭЁЭЪКЁЭЪХ ЁЭЩ▒ЁЭЪКЁЭЪХЁЭЪКЁЭЪЧЁЭЪМЁЭЪО: {new_bal:.2f} ЁЭЪГЁЭЩ║"
                        )
                        
                        kb = types.InlineKeyboardMarkup() 
                        kb.add(types.InlineKeyboardButton(text=otp, copy_text=types.CopyTextButton(text=otp))) 
                        
                        if search_msg_id: bot.edit_message_text(text, chat_id, search_msg_id, parse_mode="Markdown", reply_markup=kb) 
                        else: bot.send_message(chat_id, text, parse_mode="Markdown", reply_markup=kb) 
                        return 
            time.sleep(2) 
        if search_msg_id: 
            kb = types.InlineKeyboardMarkup() 
            kb.add(types.InlineKeyboardButton("ЁЯФД TRY AGAIN", callback_data="otp_search")) 
            bot.edit_message_text("тЭМ ЁЭЩ╜ЁЭЪШ ЁЭЩ╛ЁЭЪГЁЭЩ┐ ЁЭЩ╡ЁЭЪШЁЭЪЮЁЭЪЧЁЭЪН", chat_id, search_msg_id, reply_markup=kb) 
    finally: otp_running[chat_id] = False

# --- NUMBER PROCESSING ---
def process_number(message, edit_msg=None): 
    rid = message.text 
    if edit_msg: bot.edit_message_text("тП│ ЁЭЩ┐ЁЭЩ╗ЁЭЩ┤ЁЭЩ░ЁЭЪВЁЭЩ┤ ЁЭЪЖЁЭЩ░ЁЭЩ╕ЁЭЪГ...\nЁЯФД ЁЭЩ╜ЁЭЪДЁЭЩ╝ЁЭЩ▒ЁЭЩ┤ЁЭЪБ ЁЭЩ╢ЁЭЩ┤ЁЭЩ╜ЁЭЩ┤ЁЭЪБЁЭЩ░ЁЭЪГЁЭЩ╕ЁЭЩ╜ЁЭЩ╢...", message.chat.id, edit_msg.message_id); status_id = edit_msg.message_id 
    else: status_id = bot.send_message(message.chat.id, "тП│ ЁЭЩ┐ЁЭЩ╗ЁЭЩ┤ЁЭЩ░ЁЭЪВЁЭЩ┤ ЁЭЪЖЁЭЩ░ЁЭЩ╕ЁЭЪГ...\nЁЯФД ЁЭЩ╜ЁЭЪДЁЭЩ╝ЁЭЩ▒ЁЭЩ┤ЁЭЪБ ЁЭЩ╢ЁЭЩ┤ЁЭЩ╜ЁЭЩ┤ЁЭЪБЁЭЩ░ЁЭЪГЁЭЩ╕ЁЭЩ╜ЁЭЩ╢...").message_id
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
            kb.row(types.InlineKeyboardButton("ЁЯФД ЁЭЩ▓ЁЭЪСЁЭЪКЁЭЪЧЁЭЪРЁЭЪО ЁЭЩ╜ЁЭЪЮЁЭЪЦЁЭЪЛЁЭЪОЁЭЪЫ", callback_data="change_num"), types.InlineKeyboardButton("ЁЯФН ЁЭЩ╛ЁЭЪГЁЭЩ┐ ЁЭЪВЁЭЩ┤ЁЭЩ░ЁЭЪБЁЭЩ▓ЁЭЩ╖", callback_data="otp_search")) 
            kb.add(types.InlineKeyboardButton("ЁЯФР ЁЭЩ╛ЁЭЪГЁЭЩ┐ ЁЭЩ╢ЁЭЪБЁЭЩ╛ЁЭЪДЁЭЩ┐", url=GROUP_URL)) 
            msg = ("тЬЕ ЁЭЩ╜ЁЭЪЮЁЭЪЦЁЭЪЛЁЭЪОЁЭЪЫ ЁЭЩ░ЁЭЪЬЁЭЪЬЁЭЪТЁЭЪРЁЭЪЧЁЭЪОЁЭЪН !\nтФБтФБтФБтФБтФБтФБтФБтФБтФБтФБтФБтФБтФБтФБтФБтФБтФБтФБтФБтФБ\n\n" f"ЁЯЯв ЁЭЩ▓ЁЭЪШЁЭЪЮЁЭЪЧЁЭЪЭЁЭЪЫЁЭЪв : {get_flag(country)} {country}\n\nЁЯУЮ ЁЭЩ╜ЁЭЪЮЁЭЪЦЁЭЪЛЁЭЪОЁЭЪЫ : {full_num}\n\n" "ЁЯМ║ ЁЭЪВЁЭЪОЁЭЪЫЁЭЪЯЁЭЪТЁЭЪМЁЭЪО : ЁЭЩ╡ЁЭЪКЁЭЪМЁЭЪОЁЭЪЛЁЭЪШЁЭЪШЁЭЪФ\n\nтФБтФБтФБтФБтФБтФБтФБтФБтФБтФБтФБтФБтФБтФБтФБтФБтФБтФБтФБтФБ\nтП│ ЁЭЪЖЁЭЩ░ЁЭЩ╕ЁЭЪГЁЭЩ╕ЁЭЩ╜ЁЭЩ╢ ЁЭЩ╡ЁЭЩ╛ЁЭЪБ ЁЭЩ╛ЁЭЪГЁЭЩ┐...") 
            bot.edit_message_text(msg, message.chat.id, status_id, parse_mode="Markdown", reply_markup=kb) 
            threading.Thread(target=auto_check_otp, args=(message.chat.id, full_num, country), daemon=True).start()
        else: bot.edit_message_text("тЭМ ржирж╛ржорзНржмрж╛рж░ ржкрж╛ржУрзЯрж╛ ржпрж╛рзЯржирж┐!", message.chat.id, status_id) 
    except Exception as e: bot.edit_message_text(f"тЭМ рждрзНрж░рзБржЯрж┐: {e}", message.chat.id, status_id)

@safe_execute 
@bot.message_handler(func=lambda message: True) 
def handle_text(message): 
    if str(message.from_user.id) not in users: users[str(message.from_user.id)] = {"balance": 0}
        
    if not is_joined(message.from_user.id): 
        bot.send_message(message.chat.id, "тЪая╕П ржжрзЯрж╛ ржХрж░рзЗ ржЪрзНржпрж╛ржирзЗрж▓рзЗ ржЬрзЯрзЗржи ржХрж░рзБржиред", reply_markup=join_markup()) 
        return 
    if message.text == "ЁЯУ▒ ЁЭЩ╜ЁЭЪДЁЭЩ╝ЁЭЩ▒ЁЭЩ┤ЁЭЪБ ЁЭЩ▒ЁЭЪДЁЭЪИ": 
        msg = bot.send_message(message.chat.id, "тЪЩя╕П ЁЭЩ┐ЁЭЩ╗ЁЭЩ┤ЁЭЩ░ЁЭЪВЁЭЩ┤ ЁЭЩ┤ЁЭЩ╜ЁЭЪГЁЭЩ┤ЁЭЪБ ЁЭЪИЁЭЩ╛ЁЭЪДЁЭЪБ ЁЭЪБЁЭЩ░ЁЭЩ╜ЁЭЩ╢ЁЭЩ┤\n\nЁЯФв ЁЭЩ┤ЁЭЪбЁЭЪКЁЭЪЦЁЭЪЩЁЭЪХЁЭЪО : 2245564", parse_mode="Markdown") 
        bot.register_next_step_handler(msg, process_number) 
    elif message.text == "ЁЯУ▒ ЁЭЩ╢ЁЭЩ┤ЁЭЪГ ЁЭЩ╜ЁЭЪДЁЭЩ╝ЁЭЩ▒ЁЭЩ┤ЁЭЪБ": 
        kb = types.InlineKeyboardMarkup(row_width=1) 
        for country in service_buttons: 
            kb.add(types.InlineKeyboardButton(text=f"{get_flag(country)} {country}", callback_data=f"service_{country}")) 
        bot.send_message(message.chat.id, "ЁЯЯв ЁЭШ╛ЁЭЩЭЁЭЩдЁЭЩдЁЭЩиЁЭЩЪ ЁЭЩОЁЭЩЪЁЭЩзЁЭЩлЁЭЩЮЁЭЩШЁЭЩЪ ЁЯЯв", reply_markup=kb) 
    elif message.text == "ЁЯФР ЁЭЩ╢ЁЭЩ┤ЁЭЪГ 2ЁЭЩ╡ЁЭЩ░ ЁЭЩ▓ЁЭЩ╛ЁЭЩ│ЁЭЩ┤": 
        msg = bot.send_message(message.chat.id, "ЁЯФР ЁЭЩ┐ЁЭЩ╗ЁЭЩ┤ЁЭЩ░ЁЭЪВЁЭЩ┤ ЁЭЩ┤ЁЭЩ╜ЁЭЪГЁЭЩ┤ЁЭЪБ ЁЭЪИЁЭЩ╛ЁЭЪДЁЭЪБ ЁЭЯ╕ЁЭЩ╡ЁЭЩ░ ЁЭЩ║ЁЭЩ┤ЁЭЪИ") 
        bot.register_next_step_handler(msg, process_2fa) 
    elif message.text == "ЁЯСд ЁЭЩ┐ЁЭЪБЁЭЩ╛ЁЭЩ╡ЁЭЩ╕ЁЭЩ╗ЁЭЩ┤": 
        user_id = str(message.from_user.id)
        balance = get_firebase_balance(user_id)
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("ЁЯПж ЁЭЪЖЁЭЩ╕ЁЭЪГЁЭЩ╖ЁЭЩ│ЁЭЪБЁЭЩ░ЁЭЪЖ", callback_data="withdraw"))
        msg = (
            "тХФтХРтХРтХРтХРтХРтХРтХРтХРтХРтХРтХРтХРтХРтХРтХРтХРтХРтХРтХРтХРтХЧ\n"
            "      ЁЯСд ЁЭЪДЁЭЪВЁЭЩ┤ЁЭЪБ ЁЭЩ┐ЁЭЪБЁЭЩ╛ЁЭЩ╡ЁЭЩ╕ЁЭЩ╗ЁЭЩ┤\n"
            "тХЪтХРтХРтХРтХРтХРтХРтХРтХРтХРтХРтХРтХРтХРтХРтХРтХРтХРтХРтХРтХРтХЭ\n\n"
            f"ЁЯЖФ ЁЭЩ╕ЁЭЩ│ : {user_id}  \n"
            f"ЁЯТ░ ЁЭЩ▒ЁЭЩ░ЁЭЩ╗ЁЭЩ░ЁЭЩ╜ЁЭЩ▓ЁЭЩ┤ : {balance:.2f}$\n\n"
            "тЬЕ ЁЭЪВЁЭЪГЁЭЩ░ЁЭЪГЁЭЪДЁЭЪВ : ЁЭЩ░ЁЭЩ▓ЁЭЪГЁЭЩ╕ЁЭЪЕЁЭЩ┤"
        )
        bot.send_message(message.chat.id, msg, reply_markup=markup)
    elif message.text == "ЁЯСС ЁЭЩ░ЁЭЩ│ЁЭЩ╝ЁЭЩ╕ЁЭЩ╜ ЁЭЪВЁЭЪДЁЭЩ┐ЁЭЩ┐ЁЭЩ╛ЁЭЪБЁЭЪГ": 
        kb = types.InlineKeyboardMarkup() 
        kb.add(types.InlineKeyboardButton("ЁЯУй ржПржбржорж┐ржиржХрзЗ ржорзЗрж╕рзЗржЬ ржжрж┐ржи", url=f"tg://user?id={ADMIN_ID}")) 
        bot.send_message(message.chat.id, "ЁЯТм ржпрзЗржХрзЛржирзЛ рж╕ржорж╕рзНржпрж╛рж░ ржЬржирзНржп ржПржбржорж┐ржиржХрзЗ ржорзЗрж╕рзЗржЬ ржжрж┐ржиред", reply_markup=kb)

def process_2fa(message): 
    code = str(random.randint(100000, 999999)) 
    kb = types.InlineKeyboardMarkup() 
    kb.add(types.InlineKeyboardButton(text=code, copy_text=types.CopyTextButton(text=code))) 
    bot.send_message(message.chat.id, f"ЁЯФР ЁЭЪИЁЭЩ╛ЁЭЪДЁЭЪБ ЁЭЯ╕ЁЭЩ╡ЁЭЩ░ ЁЭЩ▓ЁЭЩ╛ЁЭЩ│ЁЭЩ┤ тЬЕ\n\n{code}", parse_mode="Markdown", reply_markup=kb)

@safe_execute 
@bot.callback_query_handler(func=lambda call: True) 
def handle_query(call): 
    if call.data == "verify_join": 
        if is_joined(call.from_user.id): bot.answer_callback_query(call.id, "тЬЕ You are verified!"); start(call.message) 
        else: bot.answer_callback_query(call.id, "тЭМ Still not joined!") 
    elif call.data == "change_num": 
        rid = user_ranges.get(call.message.chat.id) 
        if not rid: return 
        fake_msg = type("obj", (object,), {"chat": call.message.chat, "text": rid})() 
        process_number(fake_msg, edit_msg=call.message) 
    elif call.data == "otp_search": 
        if otp_running.get(call.message.chat.id): bot.answer_callback_query(call.id, "тП│ OTP Search Already Running!"); return 
        
        if received_otps.get(call.message.chat.id):
            msg = (
                "тХФтХРтХРтХРтХРтХРтХРтХРтХРтХРтХРтХРтХРтХРтХРтХРтХРтХРтХРтХРтХРтХЧ\n"
                "      тЬж ЁЭЩ╛ЁЭЪГЁЭЩ┐ ЁЭЪБЁЭЩ▓ЁЭЪЕ тЬж\n"
                "тХЪтХРтХРтХРтХРтХРтХРтХРтХРтХРтХРтХРтХРтХРтХРтХРтХРтХРтХРтХРтХРтХЭ\n\n"
                "тЮд OTP тЮд ЁЭЩ░ЁЭЪХЁЭЪЫЁЭЪОЁЭЪКЁЭЪНЁЭЪв ЁЭЪБЁЭЪОЁЭЪМЁЭЪЯЁЭЪОЁЭЪТЁЭЪЯЁЭЪОЁЭЪН тЬЕ\n\n"
                "ЁЯТО ЁЭЪВЁЭЪЭЁЭЪКЁЭЪЭЁЭЪЮЁЭЪЬ: ЁЭЩ░ЁЭЪМЁЭЪЭЁЭЪТЁЭЪЯЁЭЪО\n"
                "ЁЯПж ЁЭЪВЁЭЪОЁЭЪЫЁЭЪЯЁЭЪТЁЭЪМЁЭЪО: ЁЭЩ╛ЁЭЪГЁЭЩ┐ ЁЭЪДЁЭЪЧЁЭЪХЁЭЪШЁЭЪМЁЭЪФЁЭЪОЁЭЪН"
            )
            bot.send_message(call.message.chat.id, msg)
        else:
            user_num = user_numbers.get(call.message.chat.id); country = user_countries.get(call.message.chat.id, "Unknown") 
            search_msg = bot.send_message(call.message.chat.id, "ЁЯФН ЁЭЩ╛ЁЭЪГЁЭЩ┐ ЁЭЪВЁЭЩ┤ЁЭЩ░ЁЭЪБЁЭЩ▓ЁЭЩ╖ЁЭЩ╕ЁЭЩ╜ЁЭЩ╢...\n\nтП│ ЁЭЩ┐ЁЭЪХЁЭЪОЁЭЪКЁЭЪЬЁЭЪО ЁЭЪЖЁЭЪКЁЭЪТЁЭЪЭ...") 
            threading.Thread(target=auto_check_otp, args=(call.message.chat.id, user_num, country, search_msg.message_id), daemon=True).start() 
    elif call.data.startswith("service_"): 
        country = call.data.replace("service_", "", 1); rid = service_buttons.get(country) 
        if not rid: return 
        user_ranges[call.message.chat.id] = rid 
        fake_msg = type("obj", (object,), {"chat": call.message.chat, "text": rid})() 
        process_number(fake_msg)
    elif call.data == "withdraw":
        balance = get_firebase_balance(call.from_user.id)
        if balance < 20: bot.answer_callback_query(call.id, "тЭМ Min 20 TK!"); return
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(types.InlineKeyboardButton("ЁЯТ│ ЁЭЩ▒ЁЭЩ║ЁЭЩ░ЁЭЪВЁЭЩ╖", callback_data="bkash"), types.InlineKeyboardButton("ЁЯТ│ ЁЭЪБЁЭЩ╛ЁЭЩ▓ЁЭЩ║ЁЭЩ┤ЁЭЪГ", callback_data="rocket"))
        bot.edit_message_text("ЁЯПж ЁЭЪВЁЭЩ┤ЁЭЩ╗ЁЭЩ┤ЁЭЩ▓ЁЭЪГ ЁЭЩ┐ЁЭЩ░ЁЭЪИЁЭЩ╝ЁЭЩ┤ЁЭЩ╜ЁЭЪГ ЁЭЩ╝ЁЭЩ┤ЁЭЪГЁЭЩ╖ЁЭЩ╛ЁЭЩ│", call.message.chat.id, call.message.message_id, reply_markup=markup)
    elif call.data in ["bkash", "rocket"]:
        withdraw_data[call.from_user.id] = {"method": call.data.capitalize()}
        msg = bot.send_message(call.message.chat.id, f"ЁЯУ▒ ЁЭЩ┤ЁЭЩ╜ЁЭЪГЁЭЩ┤ЁЭЪБ ЁЭЪИЁЭЩ╛ЁЭЪДЁЭЪБ {call.data.upper()} ЁЭЩ╜ЁЭЪДЁЭЩ╝ЁЭЩ▒ЁЭЩ┤ЁЭЪБ")
        bot.register_next_step_handler(msg, get_number)
    elif call.data.startswith("approve_"):
        uid = call.data.split("_")[1]
        amount = withdraw_data.get(int(uid), {}).get("amount", 0)
        update_firebase_balance(uid, -amount)
        bot.send_message(uid, "тЬЕ ЁЭЩ┐ЁЭЩ░ЁЭЪИЁЭЩ╝ЁЭЩ┤ЁЭЩ╜ЁЭЪГ ЁЭЪВЁЭЪДЁЭЩ▓ЁЭЩ▓ЁЭЩ┤ЁЭЪВЁЭЪВ!")
        bot.edit_message_text("тЬЕ Approved", call.message.chat.id, call.message.message_id)

def get_number(message):
    withdraw_data[message.from_user.id]["number"] = message.text
    msg = bot.send_message(message.chat.id, "ЁЯТ░ ЁЭЩ┤ЁЭЩ╜ЁЭЪГЁЭЩ┤ЁЭЪБ ЁЭЩ░ЁЭЩ╝ЁЭЩ╛ЁЭЪДЁЭЩ╜ЁЭЪГ (ЁЭЩ╝ЁЭЩ╕ЁЭЩ╜ 20 ЁЭЪГЁЭЩ║)")
    bot.register_next_step_handler(msg, get_amount)

def get_amount(message):
    try:
        amount = int(message.text)
        if amount < 20: bot.send_message(message.chat.id, "тЭМ Minimum 20 TK!"); return
        withdraw_data[message.from_user.id]["amount"] = amount
        admin_text = f"ЁЯТ╕ ЁЭЩ╜ЁЭЩ┤ЁЭЪЖ ЁЭЩ┐ЁЭЩ░ЁЭЪИЁЭЩ╝ЁЭЩ┤ЁЭЩ╜ЁЭЪГ ЁЭЪБЁЭЩ┤ЁЭЪАЁЭЪДЁЭЩ┤ЁЭЪВЁЭЪГ\nЁЯСд ЁЭЩ╕ЁЭЩ│ : {message.from_user.id}\nЁЯТ░ ЁЭЩ░ЁЭЩ╝ЁЭЩ╛ЁЭЪДЁЭЩ╜ЁЭЪГ : {amount}\nЁЯУ▒ {withdraw_data[message.from_user.id]['method']} : {withdraw_data[message.from_user.id]['number']}"
        markup = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("тЬЕ ЁЭЩ░ЁЭЩ┐ЁЭЩ┐ЁЭЪБЁЭЩ╛ЁЭЪЕЁЭЩ┤", callback_data=f"approve_{message.from_user.id}"))
        bot.send_message(ADMIN_ID, admin_text, reply_markup=markup)
        bot.send_message(message.chat.id, "тЬЕ ЁЭЪВЁЭЪДЁЭЩ▒ЁЭЩ╝ЁЭЩ╕ЁЭЪГЁЭЪГЁЭЩ┤ЁЭЩ│!")
    except: bot.send_message(message.chat.id, "тЭМ Error!")

def run_bot(): 
    keep_alive() 
    while True: 
        try: 
            bot.polling(none_stop=True, interval=0, timeout=60, long_polling_timeout=60)
        except Exception: 
            time.sleep(2) 

if __name__ == "__main__": 
    run_bot()
