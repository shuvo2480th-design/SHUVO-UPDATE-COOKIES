# ===================== DUAL PANEL BOT - STEX + NEXUS =====================
import telebot
import requests
import json
import time
import re
import logging
from datetime import datetime, date
import traceback

logging.basicConfig(level=logging.INFO)

# ===================== NEXUS CONFIG =====================
NEXUS_API_KEY  = "nx_I0puoaKJBgjjv618iqRKMrylA2zZQFgaJqD3NQ"
NEXUS_BASE_URL = "https://v2.nexus-x.site/api/v1"
NEXUS_HEADERS  = {"Authorization": f"Bearer {NEXUS_API_KEY}", "Content-Type": "application/json"}

# ===================== STEX CONFIG =====================
STEX_BASE_URL = "https://api.2oo9.cloud/MXS47FLFX0U/tness/@public/api"
STEX_HEADERS  = {"mauthapi": "MUBTR1MKUBO"}

# ===================== BOT CONFIG =====================
BOT_TOKEN    = "8738544813:AAE30UcDfQDZsPYr43GCKXGoyk_h6OpqZvU"
ADMIN_ID     = "6470499890"
FIREBASE_URL = "https://shuvo-866aa-default-rtdb.firebaseio.com"
GROUP_URL    = "https://t.me/otpgurup1"
REQUIRED_CHANNELS = ["@otpgurup1", "@onlineskillshub1"]

# ===================== GLOBALS =====================
bot = telebot.TeleBot(BOT_TOKEN, threaded=True, num_threads=20)
session = requests.Session()

# Data storage
users = {}
user_numbers = {}
user_countries = {}
user_ranges = {}
user_panel = {}
user_service = {}
admin_state = {}
today_date = {}
today_earn = {}
today_otp_count = {}

# ===================== FIREBASE FUNCTIONS =====================
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
        r = session.put(
            f"{FIREBASE_URL}{path}.json",
            data=json.dumps(data, ensure_ascii=False),
            timeout=10
        )
        if r.status_code in [200, 201]:
            print(f"✅ Firebase saved: {path}")
            return True
        else:
            print(f"❌ Firebase error: {r.status_code}")
            return False
    except Exception as e:
        print(f"❌ Firebase error: {e}")
        return False

def _fb_delete(path):
    try:
        session.delete(f"{FIREBASE_URL}{path}.json", timeout=10)
    except Exception:
        pass

# ===================== BALANCE FUNCTIONS =====================
def get_firebase_balance(uid):
    uid = str(uid)
    val = _fb_get(f"/users/{uid}/balance")
    try:
        if val is not None:
            return float(val)
    except Exception:
        pass
    return 0.0

def update_firebase_balance(uid, amount):
    uid = str(uid)
    current = get_firebase_balance(uid)
    new_bal = round(current + amount, 2)
    
    try:
        _fb_put(f"/users/{uid}/balance", new_bal)
        print(f"✅ Balance updated: {uid} = {new_bal}")
    except Exception as e:
        print(f"❌ Balance error: {e}")
        return current
    
    today_str = str(date.today())
    if today_date.get(uid) != today_str:
        today_date[uid] = today_str
        today_earn[uid] = 0.0
        today_otp_count[uid] = 0
    today_earn[uid] = round(today_earn.get(uid, 0.0) + amount, 2)
    today_otp_count[uid] = today_otp_count.get(uid, 0) + 1
    return new_bal

# ===================== ADMIN RANGES =====================
admin_ranges = {}

def load_admin_ranges():
    global admin_ranges
    data = _fb_get("/admin_ranges")
    if isinstance(data, dict):
        admin_ranges = data
    else:
        admin_ranges = {"nexus": {}, "stex": {}}

def register_user(uid, name="User"):
    uid = str(uid)
    if uid not in users:
        users[uid] = {"balance": 0}
    if not _fb_get(f"/users/{uid}/registered"):
        _fb_put(f"/users/{uid}/registered", True)
    _fb_put(f"/users/{uid}/name", name)
    if not _fb_get(f"/users/{uid}/balance"):
        _fb_put(f"/users/{uid}/balance", 0)

# ===================== HELPER FUNCTIONS =====================
def is_admin(uid):
    return str(uid) == str(ADMIN_ID)

def build_inline_keyboard(rows):
    markup = telebot.types.InlineKeyboardMarkup()
    for row in rows:
        markup.row(*row)
    return markup

def make_button(text, callback_data=None, url=None):
    if url:
        return telebot.types.InlineKeyboardButton(text, url=url)
    else:
        return telebot.types.InlineKeyboardButton(text, callback_data=callback_data)

# ===================== MARKUPS =====================
def admin_panel_markup():
    return build_inline_keyboard([
        [make_button("Add Country", callback_data="adm_add_country")],
        [make_button("Del Country", callback_data="adm_del_country")],
        [make_button("Add Money", callback_data="adm_add_money")],
        [make_button("Delete Balance", callback_data="adm_del_balance")],
    ])

def panel_select_markup():
    return build_inline_keyboard([
        [make_button("NEXUS", callback_data="panel_select_nexus")],
        [make_button("STEX", callback_data="panel_select_stex")],
        [make_button("Cancel", callback_data="adm_cancel")],
    ])

def service_select_markup(panel):
    return build_inline_keyboard([
        [make_button("Facebook", callback_data=f"svc_select_{panel}_facebook")],
        [make_button("WhatsApp", callback_data=f"svc_select_{panel}_whatsapp")],
        [make_button("Telegram", callback_data=f"svc_select_{panel}_telegram")],
        [make_button("Instagram", callback_data=f"svc_select_{panel}_instagram")],
        [make_button("Back", callback_data="adm_add_country")],
    ])

def country_list_markup(panel, service):
    load_admin_ranges()
    countries = admin_ranges.get(panel, {}).get(service, [])
    
    rows = []
    rows.append([make_button("ADD NEW COUNTRY", callback_data=f"add_new_country_{panel}_{service}")])
    
    if countries:
        for i, country in enumerate(countries):
            name = country.get("name", "?")
            rid = country.get("rid", "?")
            rows.append([make_button(f"{name} ({rid})", callback_data=f"country_select_{panel}_{service}_{i}")])
    
    rows.append([make_button("Back", callback_data=f"svc_select_{panel}_{service}")])
    return build_inline_keyboard(rows)

# ===================== PROCESS NUMBER =====================
def process_number_nexus(chat_id, rid, service_name="wa"):
    nums = []
    countries = []
    api_ids = []
    
    for attempt in range(5):
        try:
            r = requests.post(
                f"{NEXUS_BASE_URL}/numbers",
                headers=NEXUS_HEADERS,
                json={"range": rid, "sid": service_name.lower(), "no_plus": False, "national": False},
                timeout=15
            )
            data = r.json()
            if data.get("ok"):
                num = str(data.get("number", "")).replace("+", "")
                country = data.get("country", "Unknown")
                api_id = data.get("id")
                
                if num not in nums:
                    nums.append(num)
                    countries.append(country)
                    api_ids.append(api_id)
                break
            time.sleep(2)
        except Exception:
            time.sleep(2)
    
    return nums, countries, api_ids

def process_number_stex(chat_id, rid):
    nums = []
    countries = []
    
    for attempt in range(5):
        try:
            r = session.post(
                f"{STEX_BASE_URL}/getnum",
                headers=STEX_HEADERS,
                json={"rid": rid},
                timeout=15
            )
            data = r.json()
            if data.get("meta", {}).get("code") == 200:
                full_num = str(data["data"]["full_number"]).replace("+", "")
                country = data["data"].get("country", "Unknown")
                
                if full_num not in nums:
                    nums.append(full_num)
                    countries.append(country)
                break
            time.sleep(2)
        except Exception:
            time.sleep(2)
    
    return nums, countries

# ===================== COMMANDS =====================
@bot.message_handler(commands=['start'])
def start(message):
    uid = str(message.from_user.id)
    chat_id = message.chat.id
    
    register_user(uid, message.from_user.first_name or "User")
    
    if is_admin(uid):
        bot.send_message(chat_id, "Welcome ADMIN!", reply_markup=build_inline_keyboard([
            [make_button("ADMIN PANEL", callback_data="admin_panel")],
            [make_button("GET NUMBER", callback_data="get_number")],
        ]))
    else:
        bot.send_message(chat_id, "Welcome to OTP Bot!", reply_markup=build_inline_keyboard([
            [make_button("GET NUMBER", callback_data="get_number")],
            [make_button("BALANCE", callback_data="check_balance")],
        ]))

@bot.message_handler(commands=['strd'])
def strd_command(message):
    uid = str(message.from_user.id)
    chat_id = message.chat.id
    
    if not is_admin(uid):
        bot.send_message(chat_id, "Admin only!")
        return
    
    welcome = "WELCOME TO DUAL PANEL OTP BOT!\n\nSTEX + NEXUS system active"
    bot.send_message(chat_id, welcome, reply_markup=build_inline_keyboard([
        [make_button("ADMIN PANEL", callback_data="admin_panel")],
        [make_button("GET NUMBER", callback_data="get_number")],
    ]))

# ===================== CALLBACK HANDLERS =====================
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    uid = str(call.from_user.id)
    cid = call.message.chat.id
    
    try:
        if call.data == "admin_panel":
            if not is_admin(uid):
                return
            bot.edit_message_text("ADMIN PANEL", cid, call.message.message_id, reply_markup=admin_panel_markup())
        
        elif call.data == "adm_add_country":
            if not is_admin(uid):
                return
            load_admin_ranges()
            bot.edit_message_text("Select Panel:", cid, call.message.message_id, reply_markup=panel_select_markup())
        
        elif call.data.startswith("panel_select_"):
            if not is_admin(uid):
                return
            panel = call.data.replace("panel_select_", "")
            admin_state[uid] = {"panel": panel}
            bot.edit_message_text(f"Select Service for {panel.upper()}:", cid, call.message.message_id, reply_markup=service_select_markup(panel))
        
        elif call.data.startswith("svc_select_"):
            if not is_admin(uid):
                return
            parts = call.data.replace("svc_select_", "").split("_", 1)
            panel = parts[0]
            service = parts[1]
            admin_state[uid] = {"panel": panel, "service": service}
            bot.edit_message_text(f"{panel.upper()} - {service.upper()}", cid, call.message.message_id, reply_markup=country_list_markup(panel, service))
        
        elif call.data == "adm_cancel":
            admin_state.pop(uid, None)
            bot.send_message(cid, "ADMIN PANEL", reply_markup=admin_panel_markup())
        
        elif call.data == "get_number":
            load_admin_ranges()
            rows = []
            services = ["facebook", "whatsapp", "telegram", "instagram"]
            for svc in services:
                rows.append([make_button(svc.upper(), callback_data=f"get_svc_{svc}")])
            bot.edit_message_text("Select Service:", cid, call.message.message_id, reply_markup=build_inline_keyboard(rows))
        
        elif call.data.startswith("get_svc_"):
            service = call.data.replace("get_svc_", "")
            load_admin_ranges()
            
            rows = []
            for panel in ["nexus", "stex"]:
                countries = admin_ranges.get(panel, {}).get(service, [])
                for i, country in enumerate(countries):
                    name = country.get("name", "?")
                    rid = country.get("rid", "?")
                    rows.append([make_button(f"{name} ({rid}) - {panel.upper()}", callback_data=f"getnum_{panel}_{service}_{rid}")])
            
            if not rows:
                bot.edit_message_text("No countries found", cid, call.message.message_id)
                return
            
            rows.append([make_button("Back", callback_data="get_number")])
            bot.edit_message_text(f"Select Country for {service.upper()}:", cid, call.message.message_id, reply_markup=build_inline_keyboard(rows))
        
        elif call.data.startswith("getnum_"):
            parts = call.data.replace("getnum_", "").split("_", 2)
            panel = parts[0]
            service = parts[1]
            rid = parts[2]
            
            status_msg = bot.edit_message_text("Getting number...", cid, call.message.message_id)
            
            if panel == "nexus":
                nums, countries, api_ids = process_number_nexus(cid, rid, service)
                user_ranges[cid] = api_ids
            else:
                nums, countries = process_number_stex(cid, rid)
                user_ranges[cid] = None
            
            if not nums:
                bot.edit_message_text("Number not available", cid, status_msg.message_id)
                return
            
            user_numbers[cid] = nums
            user_countries[cid] = countries
            user_panel[cid] = panel
            user_service[cid] = service
            
            num_text = "Your Numbers:\n\n"
            for i, num in enumerate(nums):
                num_text += f"{i+1}. {num} ({countries[i]})\n"
            num_text += f"\nPanel: {panel.upper()}"
            
            bot.edit_message_text(num_text, cid, status_msg.message_id, reply_markup=build_inline_keyboard([
                [make_button("Search OTP", callback_data="search_otp")],
                [make_button("New Number", callback_data="get_number")],
            ]))
        
        elif call.data == "search_otp":
            panel = user_panel.get(cid)
            nums = user_numbers.get(cid, [])
            
            if not nums:
                bot.edit_message_text("No number", cid, call.message.message_id)
                return
            
            otp_msg = bot.edit_message_text("Searching OTP...", cid, call.message.message_id)
            
            if panel == "nexus":
                api_ids = user_ranges.get(cid, [])
                if not api_ids:
                    bot.edit_message_text("Error searching", cid, otp_msg.message_id)
                    return
                
                for api_id in api_ids:
                    try:
                        r = requests.get(
                            f"{NEXUS_BASE_URL}/numbers/{api_id}",
                            headers=NEXUS_HEADERS,
                            timeout=15
                        )
                        data = r.json()
                        if data.get("ok") and data.get("otps"):
                            otp = data["otps"][0].get("body", "?")
                            uid_str = str(call.from_user.id)
                            new_bal = update_firebase_balance(uid_str, 0.40)
                            otp_text = f"OTP Found!\n\nOTP: {otp}\nBalance: {new_bal} TK"
                            bot.edit_message_text(otp_text, cid, otp_msg.message_id)
                            return
                    except Exception:
                        pass
            
            else:
                try:
                    r = session.get(f"{STEX_BASE_URL}/success-otp", timeout=15)
                    data = r.json()
                    if data.get("meta", {}).get("code") == 200:
                        otps = data.get("data", [])
                        if otps:
                            otp = otps[0].get("otp", "?")
                            uid_str = str(call.from_user.id)
                            new_bal = update_firebase_balance(uid_str, 0.40)
                            otp_text = f"OTP Found!\n\nOTP: {otp}\nBalance: {new_bal} TK"
                            bot.edit_message_text(otp_text, cid, otp_msg.message_id)
                            return
                except Exception:
                    pass
            
            bot.edit_message_text("OTP not found yet", cid, otp_msg.message_id)
        
        elif call.data == "check_balance":
            uid_str = str(call.from_user.id)
            balance = get_firebase_balance(uid_str)
            bot.edit_message_text(f"Balance: {balance} TK", cid, call.message.message_id)
        
        elif call.data == "adm_del_country":
            if not is_admin(uid):
                return
            load_admin_ranges()
            
            rows = []
            for panel in ["nexus", "stex"]:
                for service in ["facebook", "whatsapp", "telegram", "instagram"]:
                    countries = admin_ranges.get(panel, {}).get(service, [])
                    for i, country in enumerate(countries):
                        name = country.get("name", "?")
                        rid = country.get("rid", "?")
                        rows.append([make_button(f"{name} ({rid}) - {panel}/{service}", callback_data=f"delcountry_{panel}_{service}_{i}")])
            
            if not rows:
                bot.edit_message_text("No countries", cid, call.message.message_id)
                return
            
            rows.append([make_button("Back", callback_data="admin_panel")])
            bot.edit_message_text("Delete Country:", cid, call.message.message_id, reply_markup=build_inline_keyboard(rows))
        
        elif call.data.startswith("add_new_country_"):
            if not is_admin(uid):
                return
            parts = call.data.replace("add_new_country_", "").split("_", 1)
            panel = parts[0]
            service = parts[1]
            admin_state[uid] = {"panel": panel, "service": service, "adding": True}
            bot.send_message(cid, f"Enter Country Name for {panel.upper()} - {service.upper()}:")
        
        elif call.data.startswith("delcountry_"):
            if not is_admin(uid):
                return
            parts = call.data.replace("delcountry_", "").split("_", 2)
            panel = parts[0]
            service = parts[1]
            idx = int(parts[2])
            
            load_admin_ranges()
            countries = admin_ranges.get(panel, {}).get(service, [])
            if idx < len(countries):
                deleted = countries[idx]["name"]
                countries.pop(idx)
                
                if panel not in admin_ranges:
                    admin_ranges[panel] = {}
                admin_ranges[panel][service] = countries
                _fb_put("/admin_ranges", admin_ranges)
                
                bot.edit_message_text(f"Deleted: {deleted}", cid, call.message.message_id)
                bot.send_message(cid, "ADMIN PANEL", reply_markup=admin_panel_markup())
    
    except Exception as e:
        print(f"Callback error: {e}")

# ===================== MESSAGE HANDLER =====================
@bot.message_handler(func=lambda msg: str(msg.from_user.id) in admin_state)
def handle_admin_input(message):
    uid = str(message.from_user.id)
    if uid not in admin_state:
        return
    
    state = admin_state[uid]
    txt = message.text.strip()
    cid = message.chat.id
    
    # Adding new country flow
    if state.get("adding"):
        if "country" not in state:
            # Country name input
            admin_state[uid]["country"] = txt
            bot.send_message(cid, f"Enter Range for {txt} (e.g. 8801):")
        
        elif "range" not in state:
            # Range input
            admin_state[uid]["range"] = txt
            
            panel = state["panel"]
            service = state["service"]
            country = state["country"]
            rid = txt
            
            load_admin_ranges()
            
            if panel not in admin_ranges:
                admin_ranges[panel] = {}
            if service not in admin_ranges[panel]:
                admin_ranges[panel][service] = []
            
            # Check duplicate
            for c in admin_ranges[panel][service]:
                if c.get("name", "").lower() == country.lower():
                    c["rid"] = rid
                    break
            else:
                admin_ranges[panel][service].append({"name": country, "rid": rid})
            
            _fb_put("/admin_ranges", admin_ranges)
            
            admin_state.pop(uid, None)
            bot.send_message(cid, f"SAVED!\n\n{panel.upper()} - {service.upper()}\n{country} ({rid})\n\nSaved to Firebase!", reply_markup=admin_panel_markup())

# ===================== BOT RUN =====================
def run_bot():
    load_admin_ranges()
    while True:
        try:
            bot.polling(none_stop=True, interval=0, timeout=60, long_polling_timeout=60)
        except Exception as e:
            logging.error(traceback.format_exc())
            time.sleep(2)

if __name__ == "__main__":
    run_bot()
