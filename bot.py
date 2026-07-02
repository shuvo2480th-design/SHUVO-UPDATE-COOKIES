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
import re
import hmac
import hashlib
import base64
import struct
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
BOT_TOKEN    = "8510677584:AAE-8I9QPwW2RFkxIbzD_rAEumDgKFhg5aE"
BASE_URL     = "https://api.2oo9.cloud/MXS47FLFX0U/tness/@public/api"
HEADERS      = {"mauthapi": API_KEY}
ADMIN_ID     = "6136815573"
GROUP_URL    = "https://t.me/tem_withh"
FIREBASE_URL = "https://my-otp-bot-e8ef9-default-rtdb.firebaseio.com/"

REQUIRED_CHANNELS = ["@range_channele", "@tem_withh"]

FIXED_SERVICES = ["Facebook", "WhatsApp", "Telegram", "Instagram"]

SERVICE_ICONS = {
    "Facebook":  "F",
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
users           = {}
user_ranges     = {}
user_service    = {}
user_numbers    = {}
user_countries  = {}
received_otps   = {}
used_otps       = {}
otp_running     = {}
strd_running    = {}
withdraw_data   = {}
withdraw_status = {}
user_names      = {}

global_used_otps = {}

service_countries = {s: [] for s in FIXED_SERVICES}

# ===================== COLORED BUTTON HELPER =====================
def btn(text, callback_data=None, url=None, style="primary", copy_text=None):
    """
    style options: "primary" (blue), "success" (green), "danger" (red)
    """
    extra = {"style": style}
    if copy_text:
        extra["copy_text"] = {"text": copy_text}
    if url:
        return types.InlineKeyboardButton(text=text, url=url, **({} if not extra else {})), extra
    b = types.InlineKeyboardButton(text=text, callback_data=callback_data)
    # style inject
    b.__dict__.update(extra)
    return b

def make_button(text, callback_data=None, url=None, style="primary", copy_text_val=None):
    """
    style: primary=blue, success=green, danger=red
    Telegram bot API JSON এ style field inject করা হয়
    """
    d = {"text": text, "style": style}
    if callback_data:
        d["callback_data"] = callback_data
    if url:
        d["url"] = url
    if copy_text_val:
        d["copy_text"] = {"text": copy_text_val}
    return d

def build_inline_keyboard(rows):
    """
    rows: list of list of dicts (from make_button)
    Returns: InlineKeyboardMarkup with raw JSON override
    """
    kb = types.InlineKeyboardMarkup()
    kb.keyboard = []
    for row in rows:
        kb_row = []
        for d in row:
            if "url" in d:
                b = types.InlineKeyboardButton(text=d["text"], url=d["url"])
            elif "copy_text" in d:
                b = types.InlineKeyboardButton(
                    text=d["text"],
                    callback_data=d.get("callback_data", "noop"),
                    copy_text=types.CopyTextButton(text=d["copy_text"]["text"])
                )
            else:
                b = types.InlineKeyboardButton(
                    text=d["text"],
                    callback_data=d.get("callback_data", "noop")
                )
            # style inject করো
            if "style" in d:
                b.__dict__["style"] = d["style"]
            kb_row.append(b)
        kb.keyboard.append(kb_row)
    return kb

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

def register_user(uid, name="User"):
    uid = str(uid)
    if uid not in users:
        users[uid] = {"balance": 0}
    if not _fb_get(f"/users/{uid}/registered"):
        _fb_put(f"/users/{uid}/registered", True)
    _fb_put(f"/users/{uid}/name", name)

def load_all_users_from_firebase():
    data = _fb_get("/users")
    if isinstance(data, dict):
        for uid in data:
            if uid not in users:
                users[uid] = {"balance": 0}
            name = _fb_get(f"/users/{uid}/name")
            if name:
                user_names[uid] = name

def load_countries_from_firebase():
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

# ===================== TOTP (2FA) =====================
def _totp_generate(secret_b32: str, digits: int = 6, period: int = 30) -> str:
    try:
        secret_b32 = secret_b32.upper().strip().replace(" ", "")
        pad = (8 - len(secret_b32) % 8) % 8
        secret_bytes = base64.b32decode(secret_b32 + "=" * pad)
        counter = int(time.time()) // period
        counter_bytes = struct.pack(">Q", counter)
        h = hmac.new(secret_bytes, counter_bytes, hashlib.sha1).digest()
        offset = h[-1] & 0x0F
        code_int = struct.unpack(">I", h[offset:offset + 4])[0] & 0x7FFFFFFF
        code = str(code_int % (10 ** digits)).zfill(digits)
        return code
    except Exception:
        return None

# ===================== OTP EXTRACTION =====================
def extract_otp(message_text, phone_number=None):
    if not message_text:
        return None

    phone_digits = clean_number(phone_number) if phone_number else ""

    spaced_matches = re.findall(r'\b(\d[\d ]{2,12}\d)\b', message_text)
    for match in spaced_matches:
        joined = match.replace(" ", "")
        if not joined.isdigit():
            continue
        if phone_digits and (joined in phone_digits or phone_digits in joined):
            continue
        if 4 <= len(joined) <= 10:
            return joined

    candidates = re.findall(r'\b(\d{4,10})\b', message_text)
    for candidate in candidates:
        if phone_digits:
            if candidate in phone_digits:
                continue
            if phone_digits in candidate:
                continue
            if phone_digits[-10:] in candidate:
                continue
        if 4 <= len(candidate) <= 10:
            return candidate

    all_digits = re.sub(r'\D', '', message_text)
    if phone_digits:
        all_digits = all_digits.replace(phone_digits, "")
        all_digits = all_digits.replace(phone_digits[-10:], "")

    if len(all_digits) >= 4:
        return all_digits[-6:] if len(all_digits) >= 6 else all_digits

    return None

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

COUNTRY_NAME_MAP = {
    "ivory coast":      "CI",
    "ivory coast 2":    "CI",
    "côte d'ivoire":    "CI",
    "cote d'ivoire":    "CI",
    "cote divoire":     "CI",
    "guinea bissau":    "GW",
    "guinea-bissau":    "GW",
    "south korea":      "KR",
    "north korea":      "KP",
    "russia":           "RU",
    "tanzania":         "TZ",
    "syria":            "SY",
    "iran":             "IR",
    "vietnam":          "VN",
    "laos":             "LA",
    "moldova":          "MD",
    "congo":            "CG",
    "dr congo":         "CD",
    "democratic republic of congo": "CD",
    "palestine":        "PS",
    "kosovo":           "XK",
    "taiwan":           "TW",
    "cape verde":       "CV",
    "east timor":       "TL",
    "myanmar":          "MM",
    "swaziland":        "SZ",
    "eswatini":         "SZ",
    "macau":            "MO",
    "saint kitts":      "KN",
    "saint lucia":      "LC",
    "saint vincent":    "VC",
    "micronesia":       "FM",
    "curacao":          "CW",
}

def get_flag(country_name):
    if not country_name:
        return ""
    name_lower = country_name.lower().strip()
    if name_lower in COUNTRY_NAME_MAP:
        alpha2 = COUNTRY_NAME_MAP[name_lower]
        return "".join(chr(ord(x) + 127397) for x in alpha2.upper())
    try:
        c = pycountry.countries.lookup(country_name)
        return "".join(chr(ord(x) + 127397) for x in c.alpha_2.upper())
    except Exception:
        pass
    try:
        results = pycountry.countries.search_fuzzy(country_name)
        if results:
            return "".join(chr(ord(x) + 127397) for x in results[0].alpha_2.upper())
    except Exception:
        pass
    return ""

def is_joined(user_id):
    try:
        for ch in REQUIRED_CHANNELS:
            m = bot.get_chat_member(ch, user_id)
            if m.status not in ["member", "administrator", "creator"]:
                return False
        return True
    except Exception:
        return False

# ===================== MARKUPS (সব বাটনে style) =====================

def join_markup():
    return build_inline_keyboard([
        [make_button("📢 Join Channel 1", url="https://t.me/range_channele", style="primary")],
        [make_button("📢 Join Channel 2", url="https://t.me/tem_withh",     style="primary")],
        [make_button("✅ VERIFIED",       callback_data="verify_join",       style="success")],
    ])

def main_markup():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.row(
        types.KeyboardButton("📱 GET NUMBER"),
        types.KeyboardButton("📱 NUMBER BUY")
    )
    markup.add(
        types.KeyboardButton("🔐 GET 2FA CODE"),
        types.KeyboardButton("👑 ADMIN SUPPORT"),
        types.KeyboardButton("👤 PROFILE")
    )
    return markup

def service_menu_markup():
    rows = []
    buttons = []
    for name in FIXED_SERVICES:
        icon = SERVICE_ICONS.get(name, "📱")
        buttons.append(make_button(f"{icon} {name.upper()}", callback_data=f"sv_{name}", style="primary"))
    for i in range(0, len(buttons), 2):
        rows.append(buttons[i:i+2])
    return build_inline_keyboard(rows)

def country_menu_markup(service_name):
    rows = []
    countries = service_countries.get(service_name, [])
    if not countries:
        rows.append([make_button("⚠️ কোনো দেশ এড হয়নি", callback_data="noop", style="danger")])
    else:
        for idx, c in enumerate(countries):
            flag  = get_flag(c["name"])
            label = f"{flag} {c['name']}" if flag else c["name"]
            rows.append([make_button(label, callback_data=f"ct_{service_name}__{idx}", style="success")])
    rows.append([make_button("🔙 Back", callback_data="back_to_services", style="danger")])
    return build_inline_keyboard(rows)

def number_assigned_markup(full_num, service_name, back_cb):
    return build_inline_keyboard([
        [make_button(f"+{full_num}", callback_data="noop", style="success",
                     copy_text_val=f"+{full_num}")],
        [
            make_button("🔄 Change Number", callback_data="change_num", style="primary"),
            make_button("🔐 OTP GROUP",     url=GROUP_URL,              style="primary"),
        ],
        [make_button("🔙 BACK", callback_data=back_cb, style="danger")],
    ])

def otp_result_markup(otp):
    return build_inline_keyboard([
        [make_button(otp, callback_data="noop", style="success", copy_text_val=otp)],
    ])

def profile_markup():
    return build_inline_keyboard([
        [
            make_button("🏦 WITHDRAW",        callback_data="withdraw",  style="danger"),
            make_button("💰OTP PRICE CHECK",  callback_data="otp_price", style="success"),
        ],
        [make_button("🔙 BACK", callback_data="back_to_services", style="primary")],
    ])

def payment_method_markup():
    return build_inline_keyboard([
        [
            make_button("💳 BKASH",  callback_data="bkash",  style="primary"),
            make_button("💳 ROCKET", callback_data="rocket", style="primary"),
        ],
    ])

def admin_approve_markup(uid):
    return build_inline_keyboard([
        [
            make_button("✅ APPROVE", callback_data=f"approve_{uid}", style="success"),
            make_button("❌ REJECT",  callback_data=f"reject_{uid}",  style="danger"),
        ],
    ])

def withdraw_status_markup():
    return build_inline_keyboard([
        [make_button("𝚆𝙸𝚃𝙷𝙳𝚁𝙰𝚆 𝚂𝚃𝙰𝚃𝚄𝚂", callback_data="withdraw_status", style="primary")],
    ])

def try_again_markup():
    return build_inline_keyboard([
        [make_button("🔄 আবার চেষ্টা করুন", callback_data="change_num", style="danger")],
    ])

def otp_price_markup():
    return build_inline_keyboard([
        [make_button("🔙 BACK", callback_data="back_to_services", style="primary")],
    ])

def admin_support_markup():
    return build_inline_keyboard([
        [make_button("📩 এডমিনকে মেসেজ দিন", url=f"tg://user?id={ADMIN_ID}", style="primary")],
    ])

def back_to_services_markup():
    return build_inline_keyboard([
        [make_button("🔙 BACK", callback_data="back_to_services", style="danger")],
    ])

# ===================== /start =====================
@safe_execute
@bot.message_handler(commands=['start'])
def start(message):
    uid       = str(message.from_user.id)
    user_name = message.from_user.username or f"{message.from_user.first_name or 'User'} {message.from_user.last_name or ''}".strip()
    register_user(uid, user_name)
    user_names[uid] = user_name

    if not is_joined(message.from_user.id):
        bot.send_message(
            message.chat.id,
            "⚠️ বট ব্যবহার করার আগে নিচের দুইটি চ্যানেলে Join করুন এবং তারপর VERIFIED বাটনে চাপুন।",
            reply_markup=join_markup()
        )
        return
    welcome_text = (
        "👋𓆩𓆩WELCOME TO OTP SERViCE𓆪𓆪\n"
        " ̅ ̅ ̅ ̅ ̅ ̅ ̅ ̅ ̅ ̅ ̅ ̅ ̅ ̅ ̅\n\n"
        "🤖 WELCOME TO TEAM WITH 3.0 NUMBER BOT\n\n"
        " ̅ ̅ ̅ ̅ ̅ ̅ ̅ ̅ ̅ ̅ ̅ ̅ ̅ ̅ ̅\n\n"
        "♾️ POWERED BY Shuvoᯓᡣ𐭩"
    )
    bot.send_message(message.chat.id, welcome_text, reply_markup=main_markup())

# ===================== ADMIN COMMANDS =====================
@bot.message_handler(commands=['user'])
def count_users(message):
    if str(message.from_user.id) == ADMIN_ID:
        load_all_users_from_firebase()
        bot.reply_to(message, f"👥 মোট ইউজার সংখ্যা: {len(users)}")

@bot.message_handler(commands=['user_info'])
def user_info(message):
    if str(message.from_user.id) != ADMIN_ID:
        return
    load_all_users_from_firebase()
    if not users:
        bot.reply_to(message, "❌ কোনো ইউজার নেই!")
        return
    info_text = (
        "╔════════════════════════════════════╗\n"
        "      👥 সকল ইউজারের তথ্য 👥\n"
        "╚════════════════════════════════════╝\n\n"
    )
    for idx, uid in enumerate(sorted(users.keys()), 1):
        balance   = get_firebase_balance(uid)
        user_name = user_names.get(uid, "Unknown")
        info_text += (
            f"┌─ #{idx}\n"
            f"├ 🆔 ID: {uid}\n"
            f"├ 👤 Name: {user_name}\n"
            f"├ 💰 Balance: {balance:.2f} TK\n"
            f"└─────────────────────\n\n"
        )
    if len(info_text) > 4096:
        parts = [info_text[i:i+4000] for i in range(0, len(info_text), 4000)]
        for part in parts:
            bot.send_message(message.chat.id, part)
    else:
        bot.send_message(message.chat.id, info_text)

@bot.message_handler(commands=['send'])
def broadcast(message):
    if str(message.from_user.id) != ADMIN_ID:
        return
    text = message.text.replace("/send", "", 1).strip()
    if not text:
        bot.reply_to(message, "⚠️ কিছু লিখুন। যেমন: /send হ্যালো!")
        return
    load_all_users_from_firebase()
    count  = 0
    failed = 0
    for uid in list(users.keys()):
        try:
            bot.send_message(uid, text)
            count += 1
            time.sleep(0.05)
        except Exception:
            failed += 1
    bot.reply_to(message, f"✅ {count} জনকে পাঠানো হয়েছে।\n❌ {failed} জন ব্যর্থ।")

@bot.message_handler(commands=['add'])
def add_service(message):
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
    if str(message.from_user.id) != ADMIN_ID:
        return
    text = message.text.replace("/del", "", 1).strip()
    if "|" in text:
        service_name, country_query = [p.strip() for p in text.split("|", 1)]
        if service_name not in FIXED_SERVICES:
            bot.reply_to(message, "❌ সার্ভিসটি পাওয়া যায়নি।")
            return
        query_lower = country_query.lower()
        matched = [
            c for c in service_countries[service_name]
            if query_lower in c["name"].lower() or c["name"].lower() in query_lower
        ]
        if matched:
            deleted_names = ", ".join(c["name"] for c in matched)
            service_countries[service_name] = [
                c for c in service_countries[service_name]
                if c not in matched
            ]
            save_countries_to_firebase(service_name)
            bot.reply_to(message, f"✅ {service_name} → {deleted_names} ডিলিট হয়েছে।")
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

@bot.message_handler(commands=['price'])
def price_command(message):
    price_text = (
        "💎 𝚂𝚃𝙰𝚃𝚄𝚂 💎\n\n"
        "📲 𝚃𝙾𝙳𝙰𝚈 𝙾𝚃𝙿 𝙿𝚁𝙸𝙲𝙴 💰 𝟶.𝟼𝟶৳ 🔥\n\n"
        "✨ 𝙵𝙰𝚂𝚃 • 𝚂𝙴𝙲𝚄𝚁𝙴 • 𝚃𝚁𝚄𝚂𝚃𝙴𝙳 🚀"
    )
    bot.send_message(message.chat.id, price_text, reply_markup=otp_price_markup())

@bot.message_handler(commands=['addmoney'])
def addmoney_command(message):
    if str(message.from_user.id) != ADMIN_ID:
        return
    parts = message.text.split()
    if len(parts) != 3:
        bot.reply_to(message, "⚠️ সঠিক নিয়ম:\n/addmoney [user_id] [amount]")
        return
    uid, amount = parts[1], float(parts[2])
    new_bal = update_firebase_balance(uid, amount)
    bot.reply_to(message, f"✅ ব্যালেন্স আপডেট!\n👤 ID: {uid}\n💰 নতুন ব্যালেন্স: {new_bal} TK")

# ===================== /strd =====================
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
        "🔍 OTP SEARCHING (∞)...\n"
        "⏳ Number change na howa porynto chalu thakbe..."
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
                        msg_id   = item.get("otp_id") or item.get("id")
                        api_num2 = clean_number(item.get("number", ""))
                        cur_num2 = clean_number(current_num)
                        if msg_id in global_used_otps.get(chat_id, set()):
                            continue
                        if (api_num2 in cur_num2 or cur_num2 in api_num2) and msg_id not in used_otps.get(chat_id, []):
                            if chat_id not in used_otps:
                                used_otps[chat_id] = []
                            if chat_id not in global_used_otps:
                                global_used_otps[chat_id] = set()
                            used_otps[chat_id].append(msg_id)
                            global_used_otps[chat_id].add(msg_id)
                            otp = extract_otp(item.get("message", ""), current_num)
                            if otp is None:
                                continue
                            new_bal = update_firebase_balance(chat_id, 0.60)
                            received_otps[chat_id] = otp
                            text = (
                                "╔════════════════════╗\n"
                                f"    ➤ {current_num} ➤ 𝚁𝙲𝚅𝙴𝙳 ✅\n"
                                "╚════════════════════╝\n\n"
                                f"💰 𝙱𝙰𝙻𝙰𝙽𝙲𝙴 𝙰𝙳𝙳𝙴𝙳 : +0.60 𝚃𝙺\n\n"
                                f"🏦 𝚃𝙾𝚃𝙰𝙻 𝙱𝙰𝙻𝙰𝙽𝙲𝙴 : {new_bal:.2f} 𝚃𝙺"
                            )
                            kb = otp_result_markup(otp)
                            try:
                                bot.edit_message_text(text, chat_id, active_msg_id, reply_markup=kb)
                            except Exception:
                                try:
                                    bot.send_message(chat_id, text, reply_markup=kb)
                                except Exception:
                                    pass
                            try:
                                active_msg_id = bot.send_message(
                                    chat_id, "🔍 Next OTP SEARCHING (∞)...\n⏳ Waiting..."
                                ).message_id
                            except Exception:
                                pass
            except Exception:
                pass
            time.sleep(2)
    finally:
        strd_running[chat_id] = False

# ===================== AUTO OTP =====================
def auto_check_otp(chat_id, phone_number, search_msg_id=None):
    if otp_running.get(chat_id):
        return
    otp_running[chat_id] = True
    first_otp_found = False
    if chat_id not in used_otps:
        used_otps[chat_id] = []
    if chat_id not in global_used_otps:
        global_used_otps[chat_id] = set()
    consecutive_errors = 0
    while True:
        try:
            if user_numbers.get(chat_id) != phone_number:
                otp_running[chat_id] = False
                return
            try:
                r = session.get(f"{BASE_URL}/success-otp", timeout=15)
                r.raise_for_status()
                data = r.json()
                consecutive_errors = 0
                if data.get("meta", {}).get("code") == 200:
                    otps = data.get("data", {}).get("otps", [])
                    for item in otps:
                        api_num = clean_number(item.get("number", ""))
                        my_num  = clean_number(phone_number)
                        if not api_num or not my_num:
                            continue
                        if api_num not in my_num and my_num not in api_num:
                            continue
                        msg_id = item.get("otp_id") or item.get("id")
                        if not msg_id:
                            continue
                        if msg_id in global_used_otps[chat_id]:
                            continue
                        if msg_id in used_otps[chat_id]:
                            continue
                        used_otps[chat_id].append(msg_id)
                        global_used_otps[chat_id].add(msg_id)
                        otp = extract_otp(item.get("message", ""), phone_number)
                        if otp is None:
                            continue
                        new_bal = update_firebase_balance(chat_id, 0.60)
                        received_otps[chat_id] = otp
                        text = (
                            "╔════════════════════╗\n"
                            f"    ➤ {phone_number} ➤ 𝚁𝙲𝚅𝙴𝙳 ✅\n"
                            "╚════════════════════╝\n\n"
                            f"💰 𝙱𝙰𝙻𝙰𝙽𝙲𝙴 𝙰𝙳𝙳𝙴𝙳 : +0.60 𝚃𝙺\n\n"
                            f"🏦 𝚃𝙾𝚃𝙰𝙻 𝙱𝙰𝙻𝙰𝙽𝙲𝙴 : {new_bal:.2f} 𝚃𝙺"
                        )
                        kb = otp_result_markup(otp)
                        if not first_otp_found and search_msg_id:
                            try:
                                bot.edit_message_text(text, chat_id, search_msg_id, reply_markup=kb)
                                first_otp_found = True
                            except Exception:
                                try:
                                    bot.send_message(chat_id, text, reply_markup=kb)
                                    first_otp_found = True
                                except Exception:
                                    pass
                        else:
                            try:
                                bot.send_message(chat_id, text, reply_markup=kb)
                            except Exception:
                                pass
            except requests.exceptions.Timeout:
                consecutive_errors += 1
            except requests.exceptions.RequestException:
                consecutive_errors += 1
            except Exception:
                consecutive_errors += 1
            if consecutive_errors >= 5:
                time.sleep(5)
            else:
                time.sleep(2)
        except Exception:
            time.sleep(2)

# ===================== NUMBER PROCESSING =====================
def process_number(message, edit_msg=None, service_name="Unknown", rid=None):
    chat_id = message.chat.id
    if rid is None:
        rid = user_ranges.get(chat_id) or message.text

    if edit_msg:
        try:
            bot.edit_message_text(
                "⏳ PLEASE WAIT...\n🔄 NUMBER GENERATING...",
                chat_id, edit_msg.message_id
            )
            status_id = edit_msg.message_id
        except Exception:
            status_id = bot.send_message(
                chat_id, "⏳ PLEASE WAIT...\n🔄 NUMBER GENERATING..."
            ).message_id
    else:
        status_id = bot.send_message(
            chat_id, "⏳ PLEASE WAIT...\n🔄 NUMBER GENERATING..."
        ).message_id

    max_retries = 5
    for attempt in range(max_retries):
        try:
            r    = session.post(f"{BASE_URL}/getnum", json={"rid": rid}, timeout=15)
            data = r.json()
            if data.get("meta", {}).get("code") == 200:
                full_num = str(data["data"]["full_number"]).replace("+", "")
                country  = data["data"].get("country", "Unknown")

                otp_running[chat_id]    = False
                strd_running[chat_id]   = False
                time.sleep(0.1)

                user_numbers[chat_id]   = full_num
                user_countries[chat_id] = country
                user_ranges[chat_id]    = rid
                user_service[chat_id]   = service_name
                received_otps[chat_id]  = None
                used_otps[chat_id]      = []

                if service_name in FIXED_SERVICES:
                    back_cb = f"back_to_country_{service_name}"
                else:
                    back_cb = "back_to_services"

                kb = number_assigned_markup(full_num, service_name, back_cb)

                msg_text = (
                    "✅ Number Assigned !\n"
                    "━━━━━━━━━━━━━━━━━━━━\n\n"
                    f"🟢 Country : {get_flag(country)} {country}\n\n"
                    f"📞 Number : {full_num}\n\n"
                    f"🌺 Service : {service_name}\n\n"
                    "━━━━━━━━━━━━━━━━━━━━\n"
                    "⏳ WAITING FOR OTP..."
                )
                try:
                    bot.edit_message_text(msg_text, chat_id, status_id, reply_markup=kb)
                except Exception:
                    bot.send_message(chat_id, msg_text, reply_markup=kb)

                threading.Thread(
                    target=auto_check_otp,
                    args=(chat_id, full_num),
                    daemon=True
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

    try:
        bot.edit_message_text(
            "⚠️ এখন নাম্বার পাওয়া যাচ্ছে না, একটু পরে আবার চেষ্টা করুন।",
            chat_id, status_id, reply_markup=try_again_markup()
        )
    except Exception:
        pass

# ===================== TEXT HANDLER =====================
@safe_execute
@bot.message_handler(func=lambda m: True)
def handle_text(message):
    uid       = str(message.from_user.id)
    user_name = message.from_user.username or f"{message.from_user.first_name or 'User'} {message.from_user.last_name or ''}".strip()
    register_user(uid, user_name)
    user_names[uid] = user_name

    if not is_joined(message.from_user.id):
        bot.send_message(
            message.chat.id, "⚠️ দয়া করে চ্যানেলে জয়েন করুন।",
            reply_markup=join_markup()
        )
        return

    txt = message.text

    if txt == "📱 NUMBER BUY":
        msg = bot.send_message(
            message.chat.id,
            "⚙️ PLEASE ENTER YOUR RANGE\n\n🔢 Example : 2245564"
        )
        def _buy_handler(m):
            user_ranges[m.chat.id] = m.text
            process_number(m, service_name="NUMBER BUY", rid=m.text)
        bot.register_next_step_handler(msg, _buy_handler)

    elif txt == "📱 GET NUMBER":
        bot.send_message(
            message.chat.id,
            "📱 যে সার্ভিসের নাম্বার প্রয়োজন তা\nসিলেক্ট করুন:",
            reply_markup=service_menu_markup()
        )

    elif txt == "🔐 GET 2FA CODE":
        msg = bot.send_message(
            message.chat.id,
            "🔐 আপনার 2FA Secret Key পাঠান\n\n"
            "📌 কোথায় পাবেন:\n"
            "• Facebook/Instagram → Settings → Security → Two-Factor Authentication → Authentication App → Setup Key\n"
            "• WhatsApp → Settings → Account → Two-step verification → এর Secret Key\n\n"
            "🔑 Example: JBSWY3DPEHPK3PXP"
        )
        bot.register_next_step_handler(msg, process_2fa)

    elif txt == "👤 PROFILE":
        uid     = str(message.from_user.id)
        balance = get_firebase_balance(uid)
        msg_text = (
            "╔════════════════════╗\n"
            "      👤 𝚄𝚂𝙴𝚁 𝙿𝚁𝙾𝙵𝙸𝙻𝙴\n"
            "╚════════════════════╝\n"
            "╔════════════════════╗\n"
            f"🆔 𝙸𝙳 : {uid}\n"
            "╚════════════════════╝\n"
            "╔════════════════════╗\n"
            f"💰 𝙱𝙰𝙻𝙰𝙽𝙲𝙴 : {balance:.2f} TK\n"
            "╚════════════════════╝\n"
            "╔════════════════════╗\n"
            "✅ 𝚂𝚃𝙰𝚃𝚄𝚂 : ACTIVE\n"
            "╚════════════════════╝"
        )
        bot.send_message(message.chat.id, msg_text, reply_markup=profile_markup())

    elif txt == "👑 ADMIN SUPPORT":
        bot.send_message(
            message.chat.id, "💬 যেকোনো সমস্যার জন্য এডমিনকে মেসেজ দিন।",
            reply_markup=admin_support_markup()
        )

def process_2fa(message):
    secret_key = message.text.strip().replace(" ", "")
    code = _totp_generate(secret_key)
    if code:
        remaining = 30 - (int(time.time()) % 30)
        bot.send_message(
            message.chat.id,
            f"🔐 YOUR 2FA CODE ✅\n\n"
            f"🔑 Code : {code}\n"
            f"⏳ Valid for : {remaining} seconds",
            reply_markup=build_inline_keyboard([
                [make_button(code, callback_data="noop", style="success", copy_text_val=code)]
            ])
        )
    else:
        bot.send_message(
            message.chat.id,
            "❌ Invalid Secret Key!\n\n"
            "✅ সঠিক Base32 Key দিন।\n"
            "Example: JBSWY3DPEHPK3PXP"
        )

# ===================== CALLBACK HANDLER =====================
@safe_execute
@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    cid       = call.message.chat.id
    uid       = call.from_user.id
    user_name = call.from_user.username or f"{call.from_user.first_name or 'User'} {call.from_user.last_name or ''}".strip()
    register_user(uid, user_name)
    user_names[str(uid)] = user_name

    if call.data == "noop":
        bot.answer_callback_query(call.id)

    elif call.data == "verify_join":
        if is_joined(uid):
            bot.answer_callback_query(call.id, "✅ You are verified!")
            start(call.message)
        else:
            bot.answer_callback_query(call.id, "❌ Still not joined!")

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

    elif call.data.startswith("back_to_country_"):
        service_name = call.data.replace("back_to_country_", "")
        if service_name not in FIXED_SERVICES:
            service_name = user_service.get(cid, "")
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
        process_number(fake_msg, edit_msg=call.message, service_name=service_name, rid=rid)

    elif call.data == "change_num":
        rid          = user_ranges.get(cid)
        service_name = user_service.get(cid, "Unknown")
        if not rid:
            return
        fake_msg = type("obj", (object,), {"chat": call.message.chat, "text": rid})()
        process_number(fake_msg, edit_msg=call.message, service_name=service_name, rid=rid)

    elif call.data == "otp_search":
        if otp_running.get(cid):
            bot.answer_callback_query(call.id, "⏳ OTP Search Already Running!")
            return
        if received_otps.get(cid):
            bot.send_message(cid, (
                "╔════════════════════╗\n"
                "      ✦ OTP RCV ✦\n"
                "╚════════════════════╝\n\n"
                "➤ OTP ➤ Already Received ✅\n\n"
                "💎 Status: Active\n"
                "🏦 Service: OTP Unlocked"
            ))
        else:
            user_num   = user_numbers.get(cid)
            search_msg = bot.send_message(cid, "🔍 OTP SEARCHING...\n⏳ Please Wait...")
            threading.Thread(
                target=auto_check_otp,
                args=(cid, user_num, search_msg.message_id),
                daemon=True
            ).start()

    elif call.data == "otp_price":
        price_text = (
            "💎 𝚂𝚃𝙰𝚃𝚄𝚂 💎\n\n"
            "📲 𝚃𝙾𝙳𝙰𝚈 𝙾𝚃𝙿 𝙿𝚁𝙸𝙲𝙴 💰 𝟶.𝟼𝟶৳ 🔥\n\n"
            "✨ 𝙵𝙰𝚂𝚃 • 𝚂𝙴𝙲𝚄𝚁𝙴 • 𝚃𝚁𝚄𝚂𝚃𝙴𝙳 🚀"
        )
        try:
            bot.edit_message_text(price_text, cid, call.message.message_id, reply_markup=otp_price_markup())
        except Exception:
            bot.send_message(cid, price_text, reply_markup=otp_price_markup())

    elif call.data == "back_profile":
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

    elif call.data == "withdraw":
        balance = get_firebase_balance(uid)
        if balance < 50:
            bot.answer_callback_query(call.id, "❌ Min 50 TK!")
            return
        bot.edit_message_text(
            "🏦 SELECT PAYMENT METHOD",
            cid, call.message.message_id, reply_markup=payment_method_markup()
        )

    elif call.data in ["bkash", "rocket"]:
        withdraw_data[uid] = {"method": call.data.capitalize()}
        msg = bot.send_message(cid, f"📱 ENTER YOUR {call.data.upper()} NUMBER")
        bot.register_next_step_handler(msg, get_withdraw_number)

    elif call.data == "withdraw_status":
        uid_str     = str(uid)
        status_info = withdraw_status.get(uid_str)
        if not status_info:
            bot.answer_callback_query(call.id, "❌ কোনো withdraw request নেই।")
            return
        st     = status_info.get("status", "pending")
        amount = status_info.get("amount", 0)
        method = status_info.get("method", "")
        number = status_info.get("number", "")
        if st == "pending":
            status_text = (
                "╔════════════════════╗\n"
                "⏳ 𝚈𝙾𝚄𝚁 𝙿𝙰𝚈𝙼𝙴𝙽𝚃 𝙸𝚂 𝙿𝙴𝙽𝙳𝙸𝙽𝙶\n"
                "╚════════════════════╝\n"
                "╔════════════════════╗\n"
                f"👤 𝙸𝙳 : {uid_str}\n"
                "╚════════════════════╝\n"
                "╔════════════════════╗\n"
                f"💰 𝙰𝙼𝙾𝚄𝙽𝚃 : {amount} TK\n"
                "╚════════════════════╝\n"
                "╔════════════════════╗\n"
                f"📱 {method.upper()} : {number}\n"
                "╚════════════════════╝\n"
                "⏳ 𝙿𝚕𝚎𝚊𝚜𝚎 𝚠𝚊𝚒𝚝 𝚏𝚘𝚛 𝚊𝚗 𝙰𝚍𝚖𝚒𝚗 𝚝𝚘 𝙰𝚙𝚙𝚛𝚘𝚟𝚎 𝚈𝚘𝚞𝚛 𝚁𝚎𝚖𝚞𝚎𝚜𝚝"
            )
        elif st == "approved":
            status_text = (
                "╔════════════════════╗\n"
                "✅ 𝙿𝙰𝚈𝙼𝙴𝙽𝚃 𝚂𝚄𝙲𝙲𝙴𝚂𝚂!\n"
                "╚════════════════════╝\n"
                "╔════════════════════╗\n"
                f"👤 𝙸𝙳 : {uid_str}\n"
                "╚════════════════════╝\n"
                "╔════════════════════╗\n"
                f"💰 𝙰𝙼𝙾𝚄𝙽𝚃 : {amount} TK\n"
                "╚════════════════════╝\n"
                "╔════════════════════╗\n"
                f"📱 {method.upper()} : {number}\n"
                "╚════════════════════╝"
            )
        else:
            status_text = (
                "╔════════════════════╗\n"
                "❌ 𝙿𝙰𝚈𝙼𝙴𝙽𝚃 𝚁𝙴𝙹𝙴𝙲𝚃𝙴𝙳\n"
                "╚════════════════════╝\n"
                "╔════════════════════╗\n"
                f"👤 𝙸𝙳 : {uid_str}\n"
                "╚════════════════════╝\n"
                "╔════════════════════╗\n"
                f"💰 𝙰𝙼𝙾𝚄𝙽𝚃 : {amount} TK\n"
                "╚════════════════════╝\n"
                "╔════════════════════╗\n"
                f"📱 {method.upper()} : {number}\n"
                "╚════════════════════╝"
            )
        bot.answer_callback_query(call.id)
        bot.send_message(cid, status_text)

    elif call.data.startswith("approve_"):
        if str(uid) != ADMIN_ID:
            bot.answer_callback_query(call.id, "❌ Admin only!")
            return
        target_uid = call.data.split("_")[1]
        w          = withdraw_data.get(int(target_uid), {})
        amount     = w.get("amount", 0)
        method     = w.get("method", "")
        number     = w.get("number", "")
        update_firebase_balance(target_uid, -amount)
        withdraw_status[target_uid] = {"status": "approved", "amount": amount, "method": method, "number": number}
        try:
            approved_text = (
                "╔════════════════════╗\n"
                "✅ 𝙿𝙰𝚈𝙼𝙴𝙽𝚃 𝚂𝚄𝙲𝙲𝙴𝚂𝚂!\n"
                "╚════════════════════╝\n"
                "╔════════════════════╗\n"
                f"👤 𝙸𝙳 : {target_uid}\n"
                "╚════════════════════╝\n"
                "╔════════════════════╗\n"
                f"💰 𝙰𝙼𝙾𝚄𝙽𝚃 : {amount} TK\n"
                "╚════════════════════╝\n"
                "╔════════════════════╗\n"
                f"📱 {method.upper()} : {number}\n"
                "╚════════════════════╝"
            )
            bot.send_message(target_uid, approved_text)
        except Exception:
            pass
        bot.edit_message_text("✅ Approved", cid, call.message.message_id)

    elif call.data.startswith("reject_"):
        if str(uid) != ADMIN_ID:
            bot.answer_callback_query(call.id, "❌ Admin only!")
            return
        target_uid = call.data.split("_")[1]
        w          = withdraw_data.get(int(target_uid), {})
        amount     = w.get("amount", 0)
        method     = w.get("method", "")
        number     = w.get("number", "")
        withdraw_status[target_uid] = {"status": "rejected", "amount": amount, "method": method, "number": number}
        try:
            rejected_text = (
                "╔════════════════════╗\n"
                "❌ 𝙿𝙰𝚈𝙼𝙴𝙽𝚃 𝚁𝙴𝙹𝙴𝙲𝚃𝙴𝙳\n"
                "╚════════════════════╝\n"
                "╔════════════════════╗\n"
                f"👤 𝙸𝙳 : {target_uid}\n"
                "╚════════════════════╝\n"
                "╔════════════════════╗\n"
                f"💰 𝙰𝙼𝙾𝚄𝙽𝚃 : {amount} TK\n"
                "╚════════════════════╝\n"
                "╔════════════════════╗\n"
                f"📱 {method.upper()} : {number}\n"
                "╚════════════════════╝"
            )
            bot.send_message(target_uid, rejected_text)
        except Exception:
            pass
        bot.edit_message_text("❌ Rejected", cid, call.message.message_id)

# ===================== WITHDRAW =====================
def get_withdraw_number(message):
    withdraw_data[message.from_user.id]["number"] = message.text
    msg = bot.send_message(message.chat.id, "💰 ENTER AMOUNT (MIN 50 TK)")
    bot.register_next_step_handler(msg, get_withdraw_amount)

def get_withdraw_amount(message):
    try:
        amount = int(message.text)
        if amount < 50:
            bot.send_message(message.chat.id, "❌ Minimum 50 TK!")
            return
        uid    = message.from_user.id
        withdraw_data[uid]["amount"] = amount
        method = withdraw_data[uid]['method']
        number = withdraw_data[uid]['number']
        withdraw_status[str(uid)] = {"status": "pending", "amount": amount, "method": method, "number": number}
        user_text = (
            "╔════════════════════╗\n"
            "⏳ 𝚈𝙾𝚄𝚁 𝙿𝙰𝚈𝙼𝙴𝙽𝚃 𝙸𝚂 𝙿𝙴𝙽𝙳𝙸𝙽𝙶\n"
            "╚════════════════════╝\n"
            "╔════════════════════╗\n"
            f"👤 𝙸𝙳 : {uid}\n"
            "╚════════════════════╝\n"
            "╔════════════════════╗\n"
            f"💰 𝙰𝙼𝙾𝚄𝙽𝚃 : {amount} TK\n"
            "╚════════════════════╝\n"
            "╔════════════════════╗\n"
            f"📱 {method.upper()} : {number}\n"
            "╚════════════════════╝\n"
            "⏳ 𝙿𝚕𝚎𝚊𝚜𝚎 𝚠𝚊𝚒𝚝 𝚏𝚘𝚛 𝚊𝚗 𝙰𝚍𝚖𝚒𝚗 𝚝𝚘 𝙰𝚙𝚙𝚛𝚘𝚟𝚎 𝚈𝚘𝚞𝚛 𝚁𝚎𝚖𝚞𝚎𝚜𝚝"
        )
        bot.send_message(message.chat.id, user_text, reply_markup=withdraw_status_markup())
        admin_text = (
            "╔════════════════════╗\n"
            "💸 𝙽𝙴𝚆 𝙿𝙰𝚈𝙼𝙴𝙽𝚃 𝚁𝙴𝚀𝚄𝙴𝚂𝚃\n"
            "╚════════════════════╝\n"
            "╔════════════════════╗\n"
            f"👤 𝙸𝙳 : {uid}\n"
            "╚════════════════════╝\n"
            "╔════════════════════╗\n"
            f"💰 𝙰𝙼𝙾𝚄𝙽𝚃 : {amount} TK\n"
            "╚════════════════════╝\n"
            "╔════════════════════╗\n"
            f"📱 {method.upper()} : {number}\n"
            "╚════════════════════╝"
        )
        bot.send_message(ADMIN_ID, admin_text, reply_markup=admin_approve_markup(uid))
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
