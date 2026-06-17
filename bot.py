import telebot
from telebot import types
import requests
import time
import threading
import random
import pycountry
import logging
import traceback

# ===================== কনফিগারেশন =====================
API_KEY = "MUBTR1MKUBO"
BOT_TOKEN = "8510677584:AAG-y26-o5m7hUit-mVA1OHAKgLtcTHaxbI"
BASE_URL = "https://api.2oo9.cloud/MXS47FLFX0U/tness/@public/api"
HEADERS = {"mauthapi": API_KEY}
ADMIN_ID = "6136815573"
GROUP_URL = "https://t.me/tem_withh"

# ===================== STABLE SESSION =====================
session = requests.Session()
session.headers.update(HEADERS)

logging.basicConfig(
    level=logging.ERROR,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

bot = telebot.TeleBot(
    BOT_TOKEN,
    threaded=True,
    num_threads=20
)

user_ranges = {}
user_numbers = {}
user_countries = {}
service_buttons = {}  # {"Country Name": "RID"}

REQUIRED_CHANNELS = ["@range_channele", "@tem_withh"]
otp_running = {}   # {chat_id: True/False}

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
    markup.add(types.KeyboardButton("🔐 𝙶𝙴𝚃 2𝙵𝙰 𝙲𝙾𝙳𝙴"))
    markup.add(types.KeyboardButton("👑 𝙰𝙳𝙼𝙸𝙽 𝚂𝚄𝙿𝙿𝙾𝚁𝚃"))
    bot.send_message(message.chat.id, "👋𓆩𓆩𝚆𝙴𝙻𝙲𝙾𝙼𝙴 𝚃𝙾 𝙾𝚃𝙿 𝚂𝙴𝚁𝚅𝙸𝙲𝙴𓆪𓆪\n\n🤖 𝚃𝙴𝙰𝙼 𝚆𝙸𝚃𝙷 3.0 𝙽𝚄𝙼𝙱𝙴𝚁 𝙱𝙾𝚃", reply_markup=markup)

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
        bot.send_message(message.chat.id, "⚠️ দয়া করে চ্যানেলে জয়েন করুন।", reply_markup=join_markup())
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
    start_time = time.time()
    try:
        while time.time() - start_time < 15:
            response = session.get(f"{BASE_URL}/success-otp", timeout=10)
            data = response.json()
            if data.get("meta", {}).get("code") == 200:
                for item in data.get("data", {}).get("otps", []):
                    if clean_number(item.get("number")) in clean_number(phone_number):
                        otp = "".join(filter(str.isdigit, item.get("message", "")))[-6:]
                        text = f"✅ OTP RECEIVED\n\n🟢 Country : {get_flag(country)} {country}\n📞 Number : +{phone_number}\n\n🔑 OTP : `{otp}`"
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
    finally:
        otp_running[chat_id] = False

def process_number(message, edit_msg=None):
    rid = message.text
    if edit_msg:
        bot.edit_message_text("⏳ 𝙿𝙻𝙴𝙰𝚂𝙴 𝚆𝙰𝙸𝚃...\n🔄 𝙽𝚄𝙼𝙱𝙴𝚁 𝙶𝙴𝙽𝙴𝚁𝙰𝚃𝙸𝙽𝙶...", message.chat.id, edit_msg.message_id)
        status_id = edit_msg.message_id
    else:
        status_id = bot.send_message(message.chat.id, "⏳ 𝙿𝙻𝙴𝙰𝚂𝙴 𝚆𝙰𝙸𝚃...\n🔄 𝙽𝚄𝙼𝙱𝙴𝚁 𝙶𝙴𝙽𝙴𝚁𝙰𝚃𝙸𝙽𝙶...").message_id
    
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
            kb.add(types.InlineKeyboardButton("🔐 𝙾𝚃𝙿 𝙶𝚁𝙾𝚄𝙿", url=GROUP_URL))
            msg = ("✅ 𝙽𝚞𝚖𝚋𝚎𝚛 𝙰𝚜𝚜𝚒𝚐𝚗𝚎𝚍 !\n━━━━━━━━━━━━━━━━━━━━\n\n"
                   f"🟢 𝙲𝚘𝚞𝚗𝚝𝚛𝚢 : {get_flag(country)} {country}\n\n📞 𝙽𝚞𝚖𝚋𝚎𝚛 : `{full_num}`\n\n"
                   "🌺 𝚂𝚎𝚛𝚟𝚒𝚌𝚎 : 𝙵𝚊𝚌𝚎𝚋𝚘𝚘𝚔\n\n━━━━━━━━━━━━━━━━━━━━\n⏳ 𝚆𝙰𝙸𝚃𝙸𝙽𝙶 𝙵𝙾𝚁 𝙾𝚃𝙿...")
            bot.edit_message_text(msg, message.chat.id, status_id, parse_mode="Markdown", reply_markup=kb)
        else: bot.edit_message_text("❌ নাম্বার পাওয়া যায়নি!", message.chat.id, status_id)
    except Exception as e: bot.edit_message_text(f"❌ ত্রুটি: {e}", message.chat.id, status_id)

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
        user_num = user_numbers.get(call.message.chat.id); country = user_countries.get(call.message.chat.id, "Unknown")
        search_msg = bot.send_message(call.message.chat.id, "🔍 𝙾𝚃𝙿 𝚂𝙴𝙰𝚁𝙲𝙷𝙸𝙽𝙶...\n\n⏳ 𝙿𝚕𝚎𝚊𝚜𝚎 𝚆𝚊𝚒𝚝...")
        threading.Thread(target=auto_check_otp, args=(call.message.chat.id, user_num, country, search_msg.message_id), daemon=True).start()
    elif call.data.startswith("service_"):
        country = call.data.replace("service_", "", 1); rid = service_buttons.get(country)
        if not rid: return
        user_ranges[call.message.chat.id] = rid
        fake_msg = type("obj", (object,), {"chat": call.message.chat, "text": rid})()
        process_number(fake_msg)

def run_bot():
    while True:
        try:
            print("Bot Started...")
            bot.infinity_polling(timeout=60, long_polling_timeout=60, skip_pending=True, logger_level=logging.ERROR)
        except Exception:
            logging.error(traceback.format_exc())
            print("Bot Restarting After Crash...")
            time.sleep(5)

if __name__ == "__main__":
    run_bot()