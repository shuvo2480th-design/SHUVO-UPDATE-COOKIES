# -*- coding: utf-8 -*-

import telebot
import requests
import json
import pycountry
import threading
import time
import random
import logging
import traceback
from flask import Flask
from threading import Thread
from telebot import types

# ===================== FLASK KEEP-ALIVE =====================
app = Flask('')

@app.route('/')
def home():
    return "Bot is Running Live!"

def run_flask():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run_flask, daemon=True)
    t.start()

# ===================== কনফিগারেশন =====================
API_KEY      = "MUBTR1MKUBO"
BOT_TOKEN    = "8510677584:AAG-0cXfxYN7MTJ5puV4itwnsBNrTEPV_tw"
BASE_URL     = "https://api.2oo9.cloud/MXS47FLFX0U/tness/@public/api"
HEADERS      = {"mauthapi": API_KEY}
ADMIN_ID     = "6136815573"
GROUP_URL    = "https://t.me/tem_withh"
FIREBASE_URL = "https://my-otp-bot-e8ef9-default-rtdb.firebaseio.com/"

REQUIRED_CHANNELS = ["@range_channele", "@tem_withh"]

# ===== ৪টি হার্ডকোড সার্ভিস বাটন (কোনোভাবেই পরিবর্তন হবে না) =====
FIXED_SERVICES = ["Facebook", "WhatsApp", "Telegram", "Instagram"]

SERVICE_ICONS = {
    "Facebook":  "𝗙",
    "WhatsApp":  "💬",
    "Telegram":  "✈️",
    "Instagram": "📸",
}

# ===================== SESSION & BOT =====================
session = requests.Session()
session.headers.update(HEADERS)

logging.basicConfig(level=logging.ERROR, format="%(asctime)s - %(levelname)s - %(message)s")
bot = telebot.TeleBot(BOT_TOKEN, threaded=True, num_threads=20)

# ===================== IN-MEMORY STATE =====================
users          = {}
user_ranges    = {}
user_service   = {}
user_numbers   = {}
user_countries = {}
received_otps  = {}
used_otps      = {}
otp_running    = {}
strd_running   = {}
withdraw_data  = {}

# service_countries: শুধু দেশগুলো Firebase /service_data/ তে সেভ হয়
# { "Facebook": [{"name":"Guinea","rid":"2246545"}], "WhatsApp": [], ... }
service_countries = {s: [] for s in FIXED_SERVICES}

# ===================== FIREBASE =====================
def _fb_get(path):
    try:
        r = session.get(f"{FIREBASE_URL}{path}.json", timeout=10)
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    return None

def _fb_put(path, data):
    try:
        session.put(
            f"{FIREBASE_URL}{path}.json",
            data=json.dumps(data, ensure_ascii=False),
            timeout=10
        )
    except Exception:
        pass

def _fb_delete(path):
    try:
        session.delete(f"{FIREBASE_URL}{path}.json", timeout=10)
    except Exception:
        pass

# --- ব্যালেন্স ---
def get_firebase_balance(uid):
    val = _fb_get(f"/users/{uid}/balance")
    try:
        return float(val) if val is not None else 0.0
    except Exception:
        return 0.0

def update_firebase_balance(uid, amount):
    current = get_firebase_balance(uid)
    new_bal = round(current + amount, 2)
    _fb_put(f"/users/{uid}/balance", new_bal)
    return new_bal

# --- ইউজার রেজিস্ট্রি (Firebase-এ সেভ, কখনো ডিলিট হয় না) ---
def register_user(uid):
    uid = str(uid)
    if uid not in users:
        users[uid] = {"balance": 0}
    if not _fb_get(f"/users/{uid}/registered"):
        _fb_put(f"/users/{uid}/registered", True)

def load_all_users_from_firebase():
    """Firebase /users থেকে সব ইউজার লোড করে"""
    data = _fb_get("/users")
    if isinstance(data, dict):
        for uid in data:
            if uid not in users:
                users[uid] = {"balance": 0}

# --- সার্ভিসের দেশ লোড/সেভ ---
def load_countries_from_firebase():
    """
    শুধু /service_data/{ServiceName} থেকে দেশ লোড করবে।
    /services নোড সম্পূর্ণ ignore করবে।
    """
    for sname in FIXED_SERVICES:
        data = _fb_get(f"/service_data/{sname}")
        if isinstance(data, list):
            service_countries[sname] = [c for c in data if isinstance(c, dict) and "name" in c and "rid" in c]
        elif isinstance(data, dict):
            service_countries[sname] = [v for v in data.values() if isinstance(v, dict) and "name" in v and "rid" in v]
        else:
            service_countries[sname] = []

def save_countries_to_firebase(service_name):
    _fb_put(f"/service_data/{service_name}", service_countries[service_name])

# ===================== STARTUP =====================
load_all_users_from_firebase()
load_countries_from_firebase()

# ===================== HELPERS =====================
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
        c = pycountry.countries.lookup(country_name)
        return "".join(chr(ord(x) + 127397) for x in c.alpha_2.upper())
    except Exception:
        return "🌍"

def is_joined(user_id):
    try:
        for ch in REQUIRED_CHANNELS:
            m = bot.get_chat_member(ch, user_id)
            if m.status not in ["member", "administrator", "creator"]:
                return False
        return True
    except Exception:
        return False

def join_markup():
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(types.InlineKeyboardButton("📢 Join Channel 1", url="https://t.me/range_channele"))
    kb.add(types.InlineKeyboardButton("📢 Join Channel 2", url="https://t.me/tem_withh"))
    kb.add(types.InlineKeyboardButton("✅ VERIFIED", callback_data="verify_join"))
    return kb

def main_markup():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.row(
        types.KeyboardButton("📱 𝙶𝙴𝚃 𝙽𝚄𝙼𝙱𝙴𝚁"),
        types.KeyboardButton("📱 𝙽𝚄𝙼𝙱𝙴𝚁 𝙱𝚄𝚈")
    )
    markup.add(
        types.KeyboardButton("🔐 𝙶𝙴𝚃 2𝙵𝙰 𝙲𝙾𝙳𝙴"),
        types.KeyboardButton("👑 𝙰𝙳𝙼𝙸𝙽 𝚂𝚄𝙿𝙿𝙾𝚁𝚃"),
        types.KeyboardButton("👤 𝙿𝚁𝙾𝙵𝙸𝙻𝙴")
    )
    return markup

# সার্ভিস মেনু — সবসময় ৪টা বাটন
def service_menu_markup():
    kb = types.InlineKeyboardMarkup(row_width=2)
    buttons = []
    for name in FIXED_SERVICES:
        icon = SERVICE_ICONS.get(name, "📱")
        buttons.append(types.InlineKeyboardButton(
            text=f"{icon} {name.upper()}",
            callback_data=f"sv_{name}"
        ))
    for i in range(0, len(buttons), 2):
        kb.row(*buttons[i:i + 2])
    return kb

# দেশের লিস্ট + Back বাটন
def country_menu_markup(service_name):
    kb        = types.InlineKeyboardMarkup(row_width=1)
    countries = service_countries.get(service_name, [])
    if not countries:
        kb.add(types.InlineKeyboardButton("⚠️ কোনো দেশ এড হয়নি", callback_data="noop"))
    else:
        for idx, c in enumerate(countries):
            flag = get_flag(c["name"])
            kb.add(types.InlineKeyboardButton(
                text=f"{flag} {c['name']}",
                callback_data=f"ct_{service_name}__{idx}"
            ))
    kb.add(types.InlineKeyboardButton("🔙 Back", callback_data="back_to_services"))
    return kb

# ===================== /start =====================
@safe_execute
@bot.message_handler(commands=['start'])
def start(message):
    register_user(message.from_user.id)
    if not is_joined(message.from_user.id):
        bot.send_message(
            message.chat.id,
            "⚠️ বট ব্যবহার করার আগে নিচের দুইটি চ্যানেলে Join করুন এবং তারপর VERIFIED বাটনে চাপুন।",
            reply_markup=join_markup()
        )
        return
    welcome_text = (
        "👋𓆩𓆩𝚆𝙴𝙻𝙲𝙾𝙼𝙴 𝚃𝙾 𝙾𝚃𝙿 𝚂𝙴𝚁𝚅𝚒𝙲𝙴𓆪𓆪\n"
        "﹌﹌﹌﹌﹌﹌﹌﹌﹌﹌﹌﹌﹌﹌﹌\n\n"
        "🤖 𝚆𝙴𝙻𝙲𝙾𝙼𝙴 𝚃𝙾 𝚃𝙴𝙰𝙼 𝚆𝙸𝚃𝙷 3.0 𝙽𝚄𝙼𝙱𝙴𝚁 𝙱𝙾𝚃\n\n"
        "﹌﹌﹌﹌﹌﹌﹌﹌﹌﹌﹌﹌﹌﹌﹌\n\n"
        "♾️ 𝙿𝙾𝚆𝙴𝚁𝙴𝙳 𝙱𝚈 Shuvoᯓᡣ𐭩"
    )
    bot.send_message(message.chat.id, welcome_text, reply_markup=main_markup())

# ===================== ADMIN COMMANDS =====================
@bot.message_handler(commands=['user'])
def count_users(message):
    if str(message.from_user.id) == ADMIN_ID:
        # Firebase থেকে সর্বশেষ ইউজার সংখ্যা
        load_all_users_from_firebase()
        bot.reply_to(message, f"👥 মোট ইউজার সংখ্যা: {len(users)}")

@bot.message_handler(commands=['send'])
def broadcast(message):
    """Firebase-এ যত ইউজার আছে সবার কাছে মেসেজ পাঠাবে"""
    if str(message.from_user.id) != ADMIN_ID:
        return
    text = message.text.replace("/send", "", 1).strip()
    if not text:
        bot.reply_to(message, "⚠️ কিছু লিখুন। যেমন: /send হ্যালো!")
        return

    # Firebase থেকে সর্বশেষ ইউজার লিস্ট লোড
    load_all_users_from_firebase()

    count   = 0
    failed  = 0
    for uid in list(users.keys()):
        try:
            bot.send_message(uid, text)
            count += 1
            time.sleep(0.05)  # Telegram rate limit এড়াতে
        except Exception:
            failed += 1

    bot.reply_to(message, f"✅ {count} জনকে পাঠানো হয়েছে।\n❌ {failed} জন ব্যর্থ।")

@bot.message_handler(commands=['add'])
def add_service(message):
    """
    ফরম্যাট: /add Facebook|Guinea|2246545
    Facebook/WhatsApp/Telegram/Instagram — এই ৪টায় দেশ এড হবে।
    Firebase /service_data/{ServiceName} তে সেভ হবে।
    """
    if str(message.from_user.id) != ADMIN_ID:
        return

    raw   = message.text.replace("/add", "", 1).strip()
    parts = None

    if raw.count("|") >= 2:
        parts = [p.strip() for p in raw.split("|", 2)]
    elif raw.count("|") == 1 and ":" in raw.split("|", 1)[1]:
        left, right = raw.split("|", 1)
        country, rid = right.split(":", 1)
        parts = [left.strip(), country.strip(), rid.strip()]
    elif raw.count(":") >= 2:
        parts = [p.strip() for p in raw.split(":", 2)]
    else:
        bot.reply_to(message, "⚠️ সঠিক ফরম্যাট:\n/add Facebook|Guinea|2246545")
        return

    if len(parts) < 3 or not all(parts):
        bot.reply_to(message, "⚠️ সঠিক ফরম্যাট:\n/add Facebook|Guinea|2246545")
        return

    service_name = parts[0]
    country_name = parts[1]
    rid          = parts[2]

    if service_name not in FIXED_SERVICES:
        bot.reply_to(
            message,
            f"❌ '{service_name}' সার্ভিস নেই।\n✅ শুধু এগুলোয় এড করা যাবে:\n"
            + "\n".join(f"• {s}" for s in FIXED_SERVICES)
        )
        return

    countries = service_countries[service_name]
    found = False
    for c in countries:
        if c["name"].lower() == country_name.lower():
            c["rid"] = rid
            found    = True
            break
    if not found:
        countries.append({"name": country_name, "rid": rid})

    save_countries_to_firebase(service_name)
    bot.reply_to(
        message,
        f"✅ Added Successfully\n"
        f"🌍 Service : {service_name}\n"
        f"🌍 Country : {country_name}\n"
        f"🔢 Range   : {rid}"
    )

@bot.message_handler(commands=['del'])
def del_service(message):
    """
    /del Facebook|Guinea  → Facebook থেকে Guinea ডিলিট
    /del Facebook         → Facebook-এর সব দেশ ডিলিট
    """
    if str(message.from_user.id) != ADMIN_ID:
        return
    text = message.text.replace("/del", "", 1).strip()
    if "|" in text:
        service_name, country_name = [p.strip() for p in text.split("|", 1)]
        if service_name not in FIXED_SERVICES:
            bot.reply_to(message, "❌ সার্ভিসটি পাওয়া যায়নি।")
            return
        before = len(service_countries[service_name])
        service_countries[service_name] = [
            c for c in service_countries[service_name]
            if c["name"].lower() != country_name.lower()
        ]
        after = len(service_countries[service_name])
        if before != after:
            save_countries_to_firebase(service_name)
            bot.reply_to(message, f"✅ {service_name} → {country_name} ডিলিট হয়েছে।")
        else:
            bot.reply_to(message, "❌ দেশটি পাওয়া যায়নি।")
    else:
        service_name = text
        if service_name in FIXED_SERVICES:
            service_countries[service_name] = []
            save_countries_to_firebase(service_name)
            bot.reply_to(message, f"✅ {service_name}-এর সব দেশ ডিলিট হয়েছে।")
        else:
            bot.reply_to(message, "❌ সার্ভিসটি পাওয়া যায়নি।")

@bot.message_handler(commands=['addmoney'])
def add_money_by_admin(message):
    if str(message.from_user.id) != ADMIN_ID:
        return
    parts = message.text.split()
    if len(parts) != 3:
        bot.reply_to(message, "⚠️ সঠিক নিয়ম:\n/addmoney [user_id] [amount]")
        return
    uid, amount = parts[1], float(parts[2])
    new_bal = update_firebase_balance(uid, amount)
    bot.reply_to(message, f"✅ ব্যালেন্স আপডেট!\n👤 ID: {uid}\n💰 নতুন ব্যালেন্স: {new_bal} 𝚃𝙺")

# ===================== /strd — অনির্দিষ্টকাল OTP খোঁজা =====================
@bot.message_handler(commands=['strd'])
def strd_command(message):
    chat_id  = message.chat.id
    user_num = user_numbers.get(chat_id)
    if not user_num:
        bot.reply_to(message, "❌ আগে একটি নাম্বার নিন!")
        return
    if strd_running.get(chat_id):
        bot.reply_to(message, "⏳ ইতিমধ্যে OTP খোঁজা চলছে!")
        return
    search_msg = bot.send_message(
        chat_id,
        "🔍 𝙾𝚃𝙿 𝚂𝙴𝙰𝚁𝙲𝙷𝙸𝙽𝙶 (∞)...\n"
        "⏳ 𝙽𝚞𝚖𝚋𝚎𝚛 𝚌𝚑𝚊𝚗𝚐𝚎 𝚗𝚊 𝚑𝚘𝚠𝚊 𝚙𝚘𝚛𝚢𝚗𝚝𝚘 𝚌𝚑𝚊𝚕𝚞 𝚝𝚑𝚊𝚔𝚋𝚎..."
    )
    threading.Thread(
        target=infinite_otp_search,
        args=(chat_id, user_num, search_msg.message_id),
        daemon=True
    ).start()

def infinite_otp_search(chat_id, start_number, search_msg_id):
    strd_running[chat_id] = True
    active_msg_id = search_msg_id
    try:
        while strd_running.get(chat_id):
            current_num = user_numbers.get(chat_id)

            if current_num and current_num != start_number:
                start_number = current_num
                try:
                    active_msg_id = bot.send_message(
                        chat_id, f"🔄 নতুন নাম্বারে OTP খোঁজা শুরু: +{start_number}"
                    ).message_id
                except Exception:
                    pass

            if not current_num:
                time.sleep(2)
                continue

            try:
                r    = session.get(f"{BASE_URL}/success-otp", timeout=10)
                data = r.json()
                if data.get("meta", {}).get("code") == 200:
                    for item in data.get("data", {}).get("otps", []):
                        msg_id = item.get("id")
                        if (
                            clean_number(item.get("number", "")) in clean_number(current_num)
                            and msg_id not in used_otps.get(chat_id, [])
                        ):
                            if chat_id not in used_otps:
                                used_otps[chat_id] = []
                            used_otps[chat_id].append(msg_id)

                            otp     = "".join(filter(str.isdigit, item.get("message", "")))[-6:]
                            new_bal = update_firebase_balance(chat_id, 0.15)
                            received_otps[chat_id] = otp

                            text = (
                                "╔════════════════════╗\n"
                                f"    ➤ {current_num} ➤ 𝚁𝙲𝚅𝙴𝙳 ✅\n"
                                "╚════════════════════╝\n"
                                "💰 𝙱𝚊𝚕𝚊𝚗𝚌𝚎 𝙰𝚍𝚍𝚎𝚍: +0.15 𝚃𝙺\n"
                                f"🏦 𝚃𝚘𝚝𝚊𝚕 𝙱𝚊𝚕𝚊𝚗𝚌𝚎: {new_bal:.2f} 𝚃𝙺"
                            )
                            kb = types.InlineKeyboardMarkup()
                            kb.add(types.InlineKeyboardButton(
                                text=otp, copy_text=types.CopyTextButton(text=otp)
                            ))
                            try:
                                bot.edit_message_text(text, chat_id, active_msg_id, reply_markup=kb)
                            except Exception:
                                try:
                                    bot.send_message(chat_id, text, reply_markup=kb)
                                except Exception:
                                    pass
                            try:
                                active_msg_id = bot.send_message(
                                    chat_id, "🔍 𝙽𝚎𝚡𝚝 𝙾𝚃𝙿 𝚂𝙴𝙰𝚁𝙲𝙷𝙸𝙽𝙶 (∞)...\n⏳ 𝚆𝚊𝚒𝚝𝚒𝚗𝚐..."
                                ).message_id
                            except Exception:
                                pass
            except Exception:
                pass
            time.sleep(2)
    finally:
        strd_running[chat_id] = False

# ===================== AUTO OTP (120s) =====================
def auto_check_otp(chat_id, phone_number, search_msg_id=None):
    if otp_running.get(chat_id):
        return
    otp_running[chat_id] = True
    start_time = time.time()
    try:
        while time.time() - start_time < 120:
            if user_numbers.get(chat_id) != phone_number:
                return
            try:
                r    = session.get(f"{BASE_URL}/success-otp", timeout=10)
                data = r.json()
                if data.get("meta", {}).get("code") == 200:
                    for item in data.get("data", {}).get("otps", []):
                        msg_id = item.get("id")
                        if (
                            clean_number(item.get("number", "")) in clean_number(phone_number)
                            and msg_id not in used_otps.get(chat_id, [])
                        ):
                            if chat_id not in used_otps:
                                used_otps[chat_id] = []
                            used_otps[chat_id].append(msg_id)

                            otp     = "".join(filter(str.isdigit, item.get("message", "")))[-6:]
                            new_bal = update_firebase_balance(chat_id, 0.15)
                            received_otps[chat_id] = otp

                            text = (
                                "╔════════════════════╗\n"
                                f"    ➤ {phone_number} ➤ 𝚁𝙲𝚅𝙴𝙳 ✅\n"
                                "╚════════════════════╝\n"
                                "💰 𝙱𝚊𝚕𝚊𝚗𝚌𝚎 𝙰𝚍𝚍𝚎𝚍: +0.15 𝚃𝙺\n"
                                f"🏦 𝚃𝚘𝚝𝚊𝚕 𝙱𝚊𝚕𝚊𝚗𝚌𝚎: {new_bal:.2f} 𝚃𝙺"
                            )
                            kb = types.InlineKeyboardMarkup()
                            kb.add(types.InlineKeyboardButton(
                                text=otp, copy_text=types.CopyTextButton(text=otp)
                            ))
                            if search_msg_id:
                                try:
                                    bot.edit_message_text(text, chat_id, search_msg_id, reply_markup=kb)
                                except Exception:
                                    bot.send_message(chat_id, text, reply_markup=kb)
                            else:
                                bot.send_message(chat_id, text, reply_markup=kb)
                            return
            except Exception:
                pass
            time.sleep(2)

        if search_msg_id:
            kb = types.InlineKeyboardMarkup()
            kb.add(types.InlineKeyboardButton("🔄 TRY AGAIN", callback_data="otp_search"))
            try:
                bot.edit_message_text("❌ 𝙽𝚘 𝙾𝚃𝙿 𝙵𝚘𝚞𝚗𝚍", chat_id, search_msg_id, reply_markup=kb)
            except Exception:
                pass
    finally:
        otp_running[chat_id] = False

# ===================== NUMBER PROCESSING =====================
def process_number(message, edit_msg=None, service_name="Unknown", rid=None):
    chat_id = message.chat.id
    if rid is None:
        rid = user_ranges.get(chat_id) or message.text

    if edit_msg:
        try:
            bot.edit_message_text(
                "⏳ 𝙿𝙻𝙴𝙰𝚂𝙴 𝚆𝙰𝙸𝚃...\n🔄 𝙽𝚄𝙼𝙱𝙴𝚁 𝙶𝙴𝙽𝙴𝚁𝙰𝚃𝙸𝙽𝙶...",
                chat_id, edit_msg.message_id
            )
            status_id = edit_msg.message_id
        except Exception:
            status_id = bot.send_message(
                chat_id, "⏳ 𝙿𝙻𝙴𝙰𝚂𝙴 𝚆𝙰𝙸𝚃...\n🔄 𝙽𝚄𝙼𝙱𝙴𝚁 𝙶𝙴𝙽𝙴𝚁𝙰𝚃𝙸𝙽𝙶..."
            ).message_id
    else:
        status_id = bot.send_message(
            chat_id, "⏳ 𝙿𝙻𝙴𝙰𝚂𝙴 𝚆𝙰𝙸𝚃...\n🔄 𝙽𝚄𝙼𝙱𝙴𝚁 𝙶𝙴𝙽𝙴𝚁𝙰𝚃𝙸𝙽𝙶..."
        ).message_id

    max_retries = 5
    for attempt in range(max_retries):
        try:
            r    = session.post(f"{BASE_URL}/getnum", json={"rid": rid}, timeout=15)
            data = r.json()
            if data.get("meta", {}).get("code") == 200:
                full_num = str(data["data"]["full_number"]).replace("+", "")
                country  = data["data"].get("country", "Unknown")

                strd_running[chat_id]   = False
                user_numbers[chat_id]   = full_num
                user_countries[chat_id] = country
                user_ranges[chat_id]    = rid
                user_service[chat_id]   = service_name
                received_otps[chat_id]  = None
                used_otps[chat_id]      = []

                kb = types.InlineKeyboardMarkup(row_width=2)
                kb.add(types.InlineKeyboardButton(
                    text=f"+{full_num}",
                    copy_text=types.CopyTextButton(text=f"+{full_num}")
                ))
                kb.row(
                    types.InlineKeyboardButton("🔄 𝙲𝚑𝚊𝚗𝚐𝚎 𝙽𝚞𝚖𝚋𝚎𝚛", callback_data="change_num"),
                    types.InlineKeyboardButton("🔍 𝙾𝚃𝙿 𝚂𝙴𝙰𝚁𝙲𝙷",  callback_data="otp_search")
                )
                kb.add(types.InlineKeyboardButton("🔐 𝙾𝚃𝙿 𝙶𝚁𝙾𝚄𝙿", url=GROUP_URL))

                msg_text = (
                    "✅ 𝙽𝚞𝚖𝚋𝚎𝚛 𝙰𝚜𝚜𝚒𝚐𝚗𝚎𝚍 !\n"
                    "━━━━━━━━━━━━━━━━━━━━\n\n"
                    f"🟢 𝙲𝚘𝚞𝚗𝚝𝚛𝚢 : {get_flag(country)} {country}\n\n"
                    f"📞 𝙽𝚞𝚖𝚋𝚎𝚛 : {full_num}\n\n"
                    f"🌺 𝚂𝚎𝚛𝚟𝚒𝚌𝚎 : {service_name}\n\n"
                    "━━━━━━━━━━━━━━━━━━━━\n"
                    "⏳ 𝚆𝙰𝙸𝚃𝙸𝙽𝙶 𝙵𝙾𝚁 𝙾𝚃𝙿..."
                )
                try:
                    bot.edit_message_text(msg_text, chat_id, status_id, reply_markup=kb)
                except Exception:
                    bot.send_message(chat_id, msg_text, reply_markup=kb)

                threading.Thread(
                    target=auto_check_otp, args=(chat_id, full_num), daemon=True
                ).start()
                return

            if attempt < max_retries - 1:
                try:
                    bot.edit_message_text(
                        f"⏳ নাম্বার খোঁজা হচ্ছে... ({attempt + 2}/{max_retries})",
                        chat_id, status_id
                    )
                except Exception:
                    pass
                time.sleep(3)
        except Exception:
            if attempt < max_retries - 1:
                time.sleep(3)

    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("🔄 আবার চেষ্টা করুন", callback_data="change_num"))
    try:
        bot.edit_message_text(
            "⚠️ এখন নাম্বার পাওয়া যাচ্ছে না, একটু পরে আবার চেষ্টা করুন।",
            chat_id, status_id, reply_markup=kb
        )
    except Exception:
        pass

# ===================== TEXT HANDLER =====================
@safe_execute
@bot.message_handler(func=lambda m: True)
def handle_text(message):
    register_user(message.from_user.id)
    if not is_joined(message.from_user.id):
        bot.send_message(
            message.chat.id, "⚠️ দয়া করে চ্যানেলে জয়েন করুন।",
            reply_markup=join_markup()
        )
        return

    txt = message.text

    if txt == "📱 𝙽𝚄𝙼𝙱𝙴𝚁 𝙱𝚄𝚈":
        msg = bot.send_message(
            message.chat.id,
            "⚙️ 𝙿𝙻𝙴𝙰𝚂𝙴 𝙴𝙽𝚃𝙴𝚁 𝚈𝙾𝚄𝚁 𝚁𝙰𝙽𝙶𝙴\n\n🔢 𝙴𝚡𝚊𝚖𝚙𝚕𝚎 : 2245564"
        )
        def _buy_handler(m):
            user_ranges[m.chat.id] = m.text
            process_number(m, service_name="NUMBER BUY", rid=m.text)
        bot.register_next_step_handler(msg, _buy_handler)

    elif txt == "📱 𝙶𝙴𝚃 𝙽𝚄𝙼𝙱𝙴𝚁":
        bot.send_message(
            message.chat.id,
            "📱 যে সার্ভিসের নাম্বার প্রয়োজন তা\nসিলেক্ট করুন:",
            reply_markup=service_menu_markup()
        )

    elif txt == "🔐 𝙶𝙴𝚃 2𝙵𝙰 𝙲𝙾𝙳𝙴":
        msg = bot.send_message(message.chat.id, "🔐 𝙿𝙻𝙴𝙰𝚂𝙴 𝙴𝙽𝚃𝙴𝚁 𝚈𝙾𝚄𝚁 𝟸𝙵𝙰 𝙺𝙴𝚈")
        bot.register_next_step_handler(msg, process_2fa)

    elif txt == "👤 𝙿𝚁𝙾𝙵𝙸𝙻𝙴":
        uid     = str(message.from_user.id)
        balance = get_firebase_balance(uid)
        markup  = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🏦 𝚆𝙸𝚃𝙷𝙳𝚁𝙰𝚆", callback_data="withdraw"))
        msg_text = (
            "╔════════════════════╗\n"
            "      👤 𝚄𝚂𝙴𝚁 𝙿𝚁𝙾𝙵𝙸𝙻𝙴\n"
            "╚════════════════════╝\n\n"
            f"🆔 𝙸𝙳 : {uid}\n"
            f"💰 𝙱𝙰𝙻𝙰𝙽𝙲𝙴 : {balance:.2f} 𝚃𝙺\n\n"
            "✅ 𝚂𝚃𝙰𝚃𝚄𝚂 : 𝙰𝙲𝚃𝙸𝚅𝙴"
        )
        bot.send_message(message.chat.id, msg_text, reply_markup=markup)

    elif txt == "👑 𝙰𝙳𝙼𝙸𝙽 𝚂𝚄𝙿𝙿𝙾𝚁𝚃":
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton("📩 এডমিনকে মেসেজ দিন", url=f"tg://user?id={ADMIN_ID}"))
        bot.send_message(
            message.chat.id, "💬 যেকোনো সমস্যার জন্য এডমিনকে মেসেজ দিন।",
            reply_markup=kb
        )

def process_2fa(message):
    code = str(random.randint(100000, 999999))
    kb   = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton(text=code, copy_text=types.CopyTextButton(text=code)))
    bot.send_message(message.chat.id, f"🔐 𝚈𝙾𝚄𝚁 𝟸𝙵𝙰 𝙲𝙾𝙳𝙴 ✅\n\n{code}", reply_markup=kb)

# ===================== CALLBACK HANDLER =====================
@safe_execute
@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    cid = call.message.chat.id
    uid = call.from_user.id

    if call.data == "noop":
        bot.answer_callback_query(call.id)

    elif call.data == "verify_join":
        if is_joined(uid):
            bot.answer_callback_query(call.id, "✅ You are verified!")
            start(call.message)
        else:
            bot.answer_callback_query(call.id, "❌ Still not joined!")

    # Back → সার্ভিস মেনু
    elif call.data == "back_to_services":
        try:
            bot.edit_message_text(
                "📱 যে সার্ভিসের নাম্বার প্রয়োজন তা\nসিলেক্ট করুন:",
                cid, call.message.message_id,
                reply_markup=service_menu_markup()
            )
        except Exception:
            bot.send_message(
                cid,
                "📱 যে সার্ভিসের নাম্বার প্রয়োজন তা\nসিলেক্ট করুন:",
                reply_markup=service_menu_markup()
            )

    # সার্ভিস বাটন চাপলে → দেশের লিস্ট দেখাও
    elif call.data.startswith("sv_"):
        service_name = call.data[3:]
        if service_name not in FIXED_SERVICES:
            bot.answer_callback_query(call.id, "❌ সার্ভিস পাওয়া যায়নি।")
            return
        icon = SERVICE_ICONS.get(service_name, "📱")
        try:
            bot.edit_message_text(
                f"{icon} {service_name.upper()} — দেশ সিলেক্ট করুন:",
                cid, call.message.message_id,
                reply_markup=country_menu_markup(service_name)
            )
        except Exception:
            bot.send_message(
                cid,
                f"{icon} {service_name.upper()} — দেশ সিলেক্ট করুন:",
                reply_markup=country_menu_markup(service_name)
            )

    # দেশ বাটন চাপলে → নাম্বার নাও
    elif call.data.startswith("ct_"):
        inner = call.data[3:]
        sep   = inner.rfind("__")
        if sep == -1:
            return
        service_name = inner[:sep]
        idx          = int(inner[sep + 2:])
        if service_name not in FIXED_SERVICES:
            bot.answer_callback_query(call.id, "❌ সার্ভিস পাওয়া যায়নি।")
            return
        countries = service_countries.get(service_name, [])
        if idx >= len(countries):
            bot.answer_callback_query(call.id, "❌ দেশ পাওয়া যায়নি।")
            return
        rid = countries[idx]["rid"]
        user_ranges[cid]  = rid
        user_service[cid] = service_name
        fake_msg = type("obj", (object,), {"chat": call.message.chat, "text": rid})()
        process_number(fake_msg, service_name=service_name, rid=rid)

    # নাম্বার চেন্জ
    elif call.data == "change_num":
        rid          = user_ranges.get(cid)
        service_name = user_service.get(cid, "Unknown")
        if not rid:
            return
        fake_msg = type("obj", (object,), {"chat": call.message.chat, "text": rid})()
        process_number(fake_msg, edit_msg=call.message, service_name=service_name, rid=rid)

    # OTP Search
    elif call.data == "otp_search":
        if otp_running.get(cid):
            bot.answer_callback_query(call.id, "⏳ OTP Search Already Running!")
            return
        if received_otps.get(cid):
            bot.send_message(cid, (
                "╔════════════════════╗\n"
                "      ✦ 𝙾𝚃𝙿 𝚁𝙲𝚅 ✦\n"
                "╚════════════════════╝\n\n"
                "➤ OTP ➤ 𝙰𝚕𝚛𝚎𝚊𝚍𝚢 𝚁𝚎𝚌𝚎𝚒𝚟𝚎𝚍 ✅\n\n"
                "💎 𝚂𝚝𝚊𝚝𝚞𝚜: 𝙰𝚌𝚝𝚒𝚟𝚎\n"
                "🏦 𝚂𝚎𝚛𝚟𝚒𝚌𝚎: 𝙾𝚃𝙿 𝚄𝚗𝚕𝚘𝚌𝚔𝚎𝚍"
            ))
        else:
            user_num   = user_numbers.get(cid)
            search_msg = bot.send_message(cid, "🔍 𝙾𝚃𝙿 𝚂𝙴𝙰𝚁𝙲𝙷𝙸𝙽𝙶...\n⏳ 𝙿𝚕𝚎𝚊𝚜𝚎 𝚆𝚊𝚒𝚝...")
            threading.Thread(
                target=auto_check_otp,
                args=(cid, user_num, search_msg.message_id),
                daemon=True
            ).start()

    # Withdraw
    elif call.data == "withdraw":
        balance = get_firebase_balance(uid)
        if balance < 20:
            bot.answer_callback_query(call.id, "❌ Min 20 TK!")
            return
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(
            types.InlineKeyboardButton("💳 𝙱𝙺𝙰𝚂𝙷",  callback_data="bkash"),
            types.InlineKeyboardButton("💳 𝚁𝙾𝙲𝙺𝙴𝚃", callback_data="rocket")
        )
        bot.edit_message_text(
            "🏦 𝚂𝙴𝙻𝙴𝙲𝚃 𝙿𝙰𝚈𝙼𝙴𝙽𝚃 𝙼𝙴𝚃𝙷𝙾𝙳",
            cid, call.message.message_id, reply_markup=markup
        )

    elif call.data in ["bkash", "rocket"]:
        withdraw_data[uid] = {"method": call.data.capitalize()}
        msg = bot.send_message(cid, f"📱 𝙴𝙽𝚃𝙴𝚁 𝚈𝙾𝚄𝚁 {call.data.upper()} 𝙽𝚄𝙼𝙱𝙴𝚁")
        bot.register_next_step_handler(msg, get_withdraw_number)

    elif call.data.startswith("approve_"):
        target_uid = call.data.split("_")[1]
        amount     = withdraw_data.get(int(target_uid), {}).get("amount", 0)
        update_firebase_balance(target_uid, -amount)
        try:
            bot.send_message(target_uid, "✅ 𝙿𝙰𝚈𝙼𝙴𝙽𝚃 𝚂𝚄𝙲𝙲𝙴𝚂𝚂!")
        except Exception:
            pass
        bot.edit_message_text("✅ Approved", cid, call.message.message_id)

# ===================== WITHDRAW =====================
def get_withdraw_number(message):
    withdraw_data[message.from_user.id]["number"] = message.text
    msg = bot.send_message(message.chat.id, "💰 𝙴𝙽𝚃𝙴𝚁 𝙰𝙼𝙾𝚄𝙽𝚃 (𝙼𝙸𝙽 20 𝚃𝙺)")
    bot.register_next_step_handler(msg, get_withdraw_amount)

def get_withdraw_amount(message):
    try:
        amount = int(message.text)
        if amount < 20:
            bot.send_message(message.chat.id, "❌ Minimum 20 TK!")
            return
        uid = message.from_user.id
        withdraw_data[uid]["amount"] = amount
        admin_text = (
            f"💸 𝙽𝙴𝚆 𝙿𝙰𝚈𝙼𝙴𝙽𝚃 𝚁𝙴𝚀𝚄𝙴𝚂𝚃\n"
            f"👤 𝙸𝙳 : {uid}\n"
            f"💰 𝙰𝙼𝙾𝚄𝙽𝚃 : {amount} 𝚃𝙺\n"
            f"📱 {withdraw_data[uid]['method']} : {withdraw_data[uid]['number']}"
        )
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("✅ 𝙰𝙿𝙿𝚁𝙾𝚅𝙴", callback_data=f"approve_{uid}"))
        bot.send_message(ADMIN_ID, admin_text, reply_markup=markup)
        bot.send_message(message.chat.id, "✅ 𝚂𝚄𝙱𝙼𝙸𝚃𝚃𝙴𝙳!")
    except Exception:
        bot.send_message(message.chat.id, "❌ Error! সংখ্যা দিন।")

# ===================== BOT RUN =====================
def run_bot():
    keep_alive()
    while True:
        try:
            bot.polling(none_stop=True, interval=0, timeout=60, long_polling_timeout=60)
        except Exception:
            logging.error(traceback.format_exc())
            time.sleep(2)

if __name__ == "__main__":
    run_bot()
