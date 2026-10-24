# -*- coding: utf-8 -*-

import requests
import html as _html
import time
import telebot
import pickle
import os
import re
import random
import threading
import pycountry
import phonenumbers
from phonenumbers import geocoder
from telebot import types
from flask import Flask
from threading import Thread
from datetime import datetime, timezone, timedelta

# ===================== FLASK KEEP-ALIVE =====================
app = Flask('')

@app.route('/')
def home():
    return "Bot is Running!"

def run_flask():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run_flask, daemon=True)
    t.start()

# ===================== CONFIG =====================
BOT_TOKEN         = "8510677584:AAEqTxD7dc4EautBJ-W8deQGzvlXnsV_Gdk"
CHANNEL_ID        = "-1002670575248"

# ===== STEX CONFIG =====
API_KEY           = "MUBTR1MKUBO"
CONSOLE_URL       = "https://api.2oo9.cloud/MXS47FLFX0U/tness/@public/api/console"
HEADERS           = {"mauthapi": API_KEY}

# ===== NEXUS CONFIG =====
NEXUS_API_KEY     = "nx_y8O9Wjypv-Kugp8JDWgU3ZNd9qTaCaHfKoTZOg"
NEXUS_BASE_URL    = "https://v2.nexus-x.site/api/v1"
NEXUS_HEADERS     = {"Authorization": f"Bearer {NEXUS_API_KEY}"}

DB_FILE           = "otp_history.pkl"
NEXUS_DB_FILE     = "nexus_otp_history.pkl"
AUTO_DELETE_SEC   = 90

BD_TZ = timezone(timedelta(hours=6))

def bd_time():
    return datetime.now(BD_TZ).strftime("%H:%M")

# shared HTTP session (faster: reuses connections)
HTTP = requests.Session()
HTTP.mount('https://', requests.adapters.HTTPAdapter(pool_connections=10, pool_maxsize=50))

bot = telebot.TeleBot(BOT_TOKEN)
bot.remove_webhook()

# NEXUS API IDs যা track করব
NEXUS_TRACKING = {
    # "api_id_here": "number_here"
    # Example: "a1b2c3d4-1234-5678-90ab-cdef12345678": "+8801XXXXXXXXX"
}

# ===================== দেশ ম্যাপ =====================
COUNTRY_NAME_MAP = {
    "ivory coast": "CI", "ivory coast 2": "CI",
    "côte d'ivoire": "CI", "cote d'ivoire": "CI", "cote divoire": "CI",
    "guinea bissau": "GW", "guinea-bissau": "GW",
    "south korea": "KR", "north korea": "KP",
    "russia": "RU", "tanzania": "TZ",
    "syria": "SY", "iran": "IR",
    "vietnam": "VN", "laos": "LA",
    "moldova": "MD", "congo": "CG",
    "dr congo": "CD", "palestine": "PS",
    "taiwan": "TW", "cape verde": "CV",
    "myanmar": "MM", "eswatini": "SZ",
    "swaziland": "SZ", "east timor": "TL",
    "micronesia": "FM", "curacao": "CW",
    "kosovo": "XK", "lesotho": "LS",
    "benin": "BJ", "armenia": "AM",
    "kazakhstan": "KZ", "tajikistan": "TJ",
    "central african republic": "CF",
    "venezuela": "VE", "bolivia": "BO",
    "trinidad": "TT", "haiti": "HT",
    "cameroon": "CM", "senegal": "SN",
    "mali": "ML", "niger": "NE",
    "burkina faso": "BF", "togo": "TG",
    "ghana": "GH", "sierra leone": "SL",
    "liberia": "LR", "gambia": "GM",
    "guinea": "GN", "mauritania": "MR",
    "ethiopia": "ET", "kenya": "KE",
    "uganda": "UG", "rwanda": "RW",
    "zambia": "ZM", "zimbabwe": "ZW",
    "mozambique": "MZ", "angola": "AO",
    "malawi": "MW", "madagascar": "MG",
    "somalia": "SO", "sudan": "SD",
    "chad": "TD", "nigeria": "NG",
    "egypt": "EG", "morocco": "MA",
    "algeria": "DZ", "tunisia": "TN",
    "libya": "LY", "south africa": "ZA",
    "iraq": "IQ", "jordan": "JO",
    "saudi arabia": "SA", "yemen": "YE",
    "oman": "OM", "uae": "AE",
    "kuwait": "KW", "bahrain": "BH",
    "qatar": "QA", "lebanon": "LB",
    "pakistan": "PK", "bangladesh": "BD",
    "india": "IN", "sri lanka": "LK",
    "nepal": "NP", "indonesia": "ID",
    "philippines": "PH", "thailand": "TH",
    "malaysia": "MY", "cambodia": "KH",
    "china": "CN", "japan": "JP",
    "ukraine": "UA", "poland": "PL",
    "romania": "RO", "hungary": "HU",
    "czech": "CZ", "slovakia": "SK",
    "bulgaria": "BG", "serbia": "RS",
    "croatia": "HR", "georgia": "GE",
    "azerbaijan": "AZ", "uzbekistan": "UZ",
    "kyrgyzstan": "KG", "turkmenistan": "TM",
    "mongolia": "MN", "belarus": "BY",
    "estonia": "EE", "latvia": "LV",
    "lithuania": "LT", "mexico": "MX",
    "colombia": "CO", "peru": "PE",
    "chile": "CL", "ecuador": "EC",
    "paraguay": "PY", "uruguay": "UY",
    "cuba": "CU", "jamaica": "JM",
    "dominican": "DO", "guatemala": "GT",
    "honduras": "HN", "nicaragua": "NI",
    "costa rica": "CR", "panama": "PA",
    "el salvador": "SV", "belize": "BZ",
}

COUNTRY_LANGUAGE_MAP = {
    "VE": "Spanish", "CO": "Spanish", "MX": "Spanish", "AR": "Spanish",
    "PE": "Spanish", "CL": "Spanish", "EC": "Spanish", "BO": "Spanish",
    "PY": "Spanish", "UY": "Spanish", "CU": "Spanish", "DO": "Spanish",
    "GT": "Spanish", "HN": "Spanish", "NI": "Spanish", "CR": "Spanish",
    "PA": "Spanish", "SV": "Spanish", "BZ": "English",
    "BR": "Portuguese", "PT": "Portuguese", "AO": "Portuguese",
    "MZ": "Portuguese", "CV": "Portuguese", "GW": "Portuguese",
    "FR": "French", "BE": "French", "SN": "French", "ML": "French",
    "BF": "French", "NE": "French", "TG": "French", "BJ": "French",
    "CI": "French", "CM": "French", "CF": "French", "CD": "French",
    "CG": "French", "GA": "French", "GN": "French", "MG": "French",
    "RW": "French", "HT": "French", "DJ": "French",
    "DE": "German", "AT": "German", "CH": "German",
    "RU": "Russian", "BY": "Russian", "KZ": "Russian",
    "UA": "Ukrainian", "PL": "Polish", "RO": "Romanian",
    "CN": "Chinese", "TW": "Chinese", "HK": "Chinese",
    "JP": "Japanese", "KR": "Korean", "KP": "Korean",
    "SA": "Arabic", "EG": "Arabic", "IQ": "Arabic", "SY": "Arabic",
    "JO": "Arabic", "LB": "Arabic", "YE": "Arabic", "OM": "Arabic",
    "AE": "Arabic", "KW": "Arabic", "BH": "Arabic", "QA": "Arabic",
    "MA": "Arabic", "DZ": "Arabic", "TN": "Arabic", "LY": "Arabic",
    "SD": "Arabic", "SO": "Arabic", "MR": "Arabic",
    "IN": "Hindi", "NP": "Nepali", "BD": "Bengali",
    "PK": "Urdu", "LK": "Sinhala", "MM": "Burmese",
    "TH": "Thai", "VN": "Vietnamese", "KH": "Khmer",
    "ID": "Indonesian", "MY": "Malay", "PH": "Filipino",
    "TR": "Turkish", "AZ": "Azerbaijani", "UZ": "Uzbek",
    "TM": "Turkmen", "KG": "Kyrgyz", "TJ": "Tajik",
    "AM": "Armenian", "GE": "Georgian", "MN": "Mongolian",
    "IR": "Persian", "AF": "Dari", "IL": "Hebrew",
    "ET": "Amharic", "NG": "English", "GH": "English",
    "KE": "English", "UG": "English", "TZ": "English",
    "ZM": "English", "ZW": "English", "MW": "English",
    "ZA": "English", "NA": "English", "BW": "English",
    "LS": "English", "SL": "English", "LR": "English",
    "GM": "English", "US": "English", "GB": "English",
    "CA": "English", "AU": "English", "NZ": "English",
    "JM": "English", "TT": "English",
}

def get_alpha2(country_name):
    if not country_name:
        return None
    name_lower = country_name.lower().strip()
    if name_lower in COUNTRY_NAME_MAP:
        return COUNTRY_NAME_MAP[name_lower]
    try:
        c = pycountry.countries.lookup(country_name)
        return c.alpha_2
    except Exception:
        pass
    try:
        results = pycountry.countries.search_fuzzy(country_name)
        if results:
            return results[0].alpha_2
    except Exception:
        pass
    return None

def get_flag(country_name):
    alpha2 = get_alpha2(country_name)
    if alpha2:
        return "".join(chr(ord(x) + 127397) for x in alpha2.upper())
    return "🌐"

def get_short_code(country_name):
    alpha2 = get_alpha2(country_name)
    if alpha2:
        return f"#{alpha2.upper()}"
    return "#??"

def get_language(alpha2):
    if not alpha2:
        return "English"
    return COUNTRY_LANGUAGE_MAP.get(alpha2.upper(), "English")

def get_country_from_number(number):
    try:
        clean = re.sub(r'\D', '', str(number))
        parsed = phonenumbers.parse("+" + clean, None)
        name = geocoder.country_name_for_number(parsed, "en")
        return name if name else "Unknown"
    except Exception:
        return "Unknown"

# ===================== PREMIUM EMOJI / FLAGS =====================
# iso -> (flag, custom_emoji_id) ; service NAME -> (emoji, custom_emoji_id)
PREMIUM_FLAGS = {'US': ('🇺🇸', '5913463998522592692'), 'UA': ('🇺🇦', '5911406692007941050'), 'PL': ('🇵🇱', '5913550391789752571'), 'KZ': ('🇰🇿', '5913724621433082323'), 'CN': ('🇨🇳', '5913779335021466780'), 'AZ': ('🇦🇿', '5911197578640233518'), 'EU': ('🇪🇺', '5911106310585193018'), 'AM': ('🇦🇲', '5913272455866093666'), 'RU': ('🇷🇺', '5913274246867456342'), 'UZ': ('🇺🇿', '5911051846104912282'), 'DE': ('🇩🇪', '5911096835887337583'), 'JP': ('🇯🇵', '5913293711659241040'), 'TR': ('🇹🇷', '5910995113881901195'), 'BY': ('🇧🇾', '5911011185649521599'), 'GB': ('🇬🇧', '5913443365499703513'), 'IN': ('🇮🇳', '5913754823643107921'), 'BR': ('🇧🇷', '5911148568768418614'), 'ZM': ('🇿🇲', '5913564754160389778'), 'YE': ('🇾🇪', '5913346492512341993'), 'VN': ('🇻🇳', '5913428887164949581'), 'VA': ('🇻🇦', '5911211932420938860'), 'VU': ('🇻🇺', '5913511535220625585'), 'UY': ('🇺🇾', '5913623088406204470'), 'AE': ('🇦🇪', '5913726554168365343'), 'UG': ('🇺🇬', '5913488939397681980'), 'TM': ('🇹🇲', '5913315521503170180'), 'TN': ('🇹🇳', '5911332947419468671'), 'TG': ('🇹🇬', '5913423260757790970'), 'TH': ('🇹🇭', '5913617968805187987'), 'TZ': ('🇹🇿', '5911418949844603556'), 'TJ': ('🇹🇯', '5911287639809463107'), 'CH': ('🇨🇭', '5913271227505448072'), 'SE': ('🇸🇪', '5911156510162949403'), 'SZ': ('🇸🇿', '5913374525763883286'), 'SR': ('🇸🇷', '5913275539652611719'), 'SD': ('🇸🇩', '5911387497799094470'), 'ES': ('🇪🇸', '5911193287967904547'), 'LK': ('🇱🇰', '5911293163137406640'), 'SS': ('🇸🇸', '5911406262511211744'), 'ZA': ('🇿🇦', '5911203119148044594'), 'SO': ('🇸🇴', '5911397852965244436'), 'SB': ('🇸🇧', '5911482712929080608'), 'SI': ('🇸🇮', '5913431983836368644'), 'SK': ('🇸🇰', '5913751666842145020'), 'SG': ('🇸🇬', '5911531460808051849'), 'SL': ('🇸🇱', '5911210450657218661'), 'SC': ('🇸🇨', '5911185183364616913'), 'RS': ('🇷🇸', '5913592598433369871'), 'SN': ('🇸🇳', '5910995302860461643'), 'ST': ('🇸🇹', '5913574331937462345'), 'SM': ('🇸🇲', '5913587968458625465'), 'WS': ('🇼🇸', '5913325971158602854'), 'KN': ('🇰🇳', '5913691898077253637'), 'VC': ('🇻🇨', '5911318941531116255'), 'LC': ('🇱🇨', '5911243659344351824'), 'PS': ('🇵🇸', '5913684768431541668'), 'RW': ('🇷🇼', '5911455229433352234'), 'RO': ('🇷🇴', '5913460373570195273'), 'QA': ('🇶🇦', '5911260864983339619'), 'PR': ('🇵🇷', '5911504350974317480'), 'PT': ('🇵🇹', '5911023653939581472'), 'PH': ('🇵🇭', '5911268638874145162'), 'PE': ('🇵🇪', '5911207993935925780'), 'PY': ('🇵🇾', '5911014265141072316'), 'PG': ('🇵🇬', '5911107251183030903'), 'PA': ('🇵🇦', '5913428968769327174'), 'PW': ('🇵🇼', '5911283903187915549'), 'PK': ('🇵🇰', '5913705895375672082'), 'OM': ('🇴🇲', '5913570801474343473'), 'NO': ('🇳🇴', '5913617397574537046'), 'NG': ('🇳🇬', '5911143844304393105'), 'NE': ('🇳🇪', '5911270086278124251'), 'NZ': ('🇳🇿', '5913640044937089340'), 'NL': ('🇳🇱', '5913367645226275100'), 'NP': ('🇳🇵', '5913496520014958723'), 'NA': ('🇳🇦', '5911108535378252443'), 'MZ': ('🇲🇿', '5911333419865871464'), 'MA': ('🇲🇦', '5911482111633658301'), 'ME': ('🇲🇪', '5913239436157522151'), 'MN': ('🇲🇳', '5911041383564580038'), 'MC': ('🇲🇨', '5911245347266500057'), 'MD': ('🇲🇩', '5913456847402045950'), 'MV': ('🇲🇻', '5913501399097806832'), 'ML': ('🇲🇱', '5911305266355245916'), 'MT': ('🇲🇹', '5911023714069123567'), 'MX': ('🇲🇽', '5913687302462246518'), 'MY': ('🇲🇾', '5913654360063087453'), 'KE': ('🇰🇪', '5911154710571651231'), 'MG': ('🇲🇬', '5913766918271012920'), 'MK': ('🇲🇰', '5913394029210374721'), 'LU': ('🇱🇺', '5913390842344640293'), 'LT': ('🇱🇹', '5911172315642595523'), 'LI': ('🇱🇮', '5911166650580734660'), 'LY': ('🇱🇾', '5911236989260140996'), 'LR': ('🇱🇷', '5913324167272337727'), 'KI': ('🇰🇮', '5911294443037660118'), 'XK': ('🇽🇰', '5911433681582429010'), 'KW': ('🇰🇼', '5913290705182134003'), 'KG': ('🇰🇬', '5911202161370337549'), 'LA': ('🇱🇦', '5913718526874489279'), 'LV': ('🇱🇻', '5913738489882480243'), 'LB': ('🇱🇧', '5911504273664905447'), 'LS': ('🇱🇸', '5911059881988723711'), 'ID': ('🇮🇩', '5913479361620611038'), 'IR': ('🇮🇷', '5911308891307643032'), 'IQ': ('🇮🇶', '5911382442622587735'), 'IE': ('🇮🇪', '5913440715504881532'), 'IL': ('🇮🇱', '5911471936856134692'), 'IT': ('🇮🇹', '5913688444923547525'), 'JM': ('🇯🇲', '5913232280742006526'), 'JO': ('🇯🇴', '5913234136167878475'), 'IS': ('🇮🇸', '5911047899029967246'), 'HU': ('🇭🇺', '5913767635530551104'), 'HN': ('🇭🇳', '5911406889576436289'), 'HT': ('🇭🇹', '5913459789454643194'), 'GY': ('🇬🇾', '5913579412883771480'), 'GW': ('🇬🇼', '5911398694778836149'), 'GN': ('🇬🇳', '5913471858312744319'), 'GT': ('🇬🇹', '5913324858762072330'), 'GD': ('🇬🇩', '5913228063084121946'), 'GR': ('🇬🇷', '5911210399117611448'), 'GH': ('🇬🇭', '5913391155877252952'), 'GE': ('🇬🇪', '5913434771270144023'), 'GM': ('🇬🇲', '5913657267755945883'), 'GA': ('🇬🇦', '5911037896051137264'), 'FR': ('🇫🇷', '5913605586414473124'), 'FI': ('🇫🇮', '5911041344909873378'), 'FJ': ('🇫🇯', '5911393832875856716'), 'ET': ('🇪🇹', '5911078333168227043'), 'DO': ('🇩🇴', '5911152099231536123'), 'TL': ('🇹🇱', '5911141915864076479'), 'EC': ('🇪🇨', '5911273865849347408'), 'EG': ('🇪🇬', '5913694831539916769'), 'SV': ('🇸🇻', '5913238624408703010'), 'EE': ('🇪🇪', '5910986042910969906'), 'DM': ('🇩🇲', '5911377121158107430'), 'DJ': ('🇩🇯', '5911407709915190157'), 'DK': ('🇩🇰', '5911206009661034712'), 'CY': ('🇨🇾', '5911023550860366409'), 'HR': ('🇭🇷', '5913692684056269311'), 'CR': ('🇨🇷', '5911261745451635030'), 'CG': ('🇨🇬', '5911338788574990168'), 'CD': ('🇨🇩', '5913770362834783827'), 'KM': ('🇰🇲', '5911338582416560604'), 'KH': ('🇰🇭', '5913699998385573485'), 'CM': ('🇨🇲', '5911172109484167745'), 'CA': ('🇨🇦', '5913623736946265914'), 'CV': ('🇨🇻', '5913571501554012193'), 'CF': ('🇨🇫', '5913443245240619222'), 'TD': ('🇹🇩', '5913299849167507310'), 'CZ': ('🇨🇿', '5911198691036764307'), 'CL': ('🇨🇱', '5911471936856134692'), 'CO': ('🇨🇴', '5913773060074246009'), 'BI': ('🇧🇮', '5913766441529642752'), 'BW': ('🇧🇼', '5911513782722499475'), 'BA': ('🇧🇦', '5913700002680541032'), 'BO': ('🇧🇴', '5913638795101606133'), 'BT': ('🇧🇹', '5913236734623093021'), 'BJ': ('🇧🇯', '5913735869952430547'), 'AR': ('🇦🇷', '5913573356979884082'), 'AU': ('🇦🇺', '5913632326880858455'), 'AT': ('🇦🇹', '5911338831524664592'), 'BS': ('🇧🇸', '5911451643135660214'), 'BH': ('🇧🇭', '5913581663446634403'), 'BD': ('🇧🇩', '5911365056594973179'), 'BE': ('🇧🇪', '5913529642802745141'), 'BZ': ('🇧🇿', '5913355005137522807'), 'AO': ('🇦🇴', '5913753316109586411'), 'AD': ('🇦🇩', '5911314702398396902'), 'DZ': ('🇩🇿', '5913782968563800236'), 'AL': ('🇦🇱', '5911357458797826163'), 'AF': ('🇦🇫', '5913492040364068694'), 'ZW': ('🇿🇼', '5911092502265336396'), 'CU': ('🇨🇺', '5431551436502611633'), 'KP': ('🇰🇵', '5434142701941437163'), 'VE': ('🇻🇪', '5434009132753499322'), 'SY': ('🇸🇾', '5433910876786670092'), 'MM': ('🇲🇲', '5294254478944393569'), 'NI': ('🇳🇮', '5334807849418003620'), 'KR': ('🇰🇷', '5913371673905598425'), 'GQ': ('🇬🇶', '5911306279967529251'), 'GL': ('🇬🇱', '5292014752283774878'), 'FO': ('🇫🇴', '5296469342039327674'), 'CI': ('🇨🇮', '5222233374948602940'), 'BN': ('🇧🇳', '5911336409163109113'), 'BG': ('🇧🇬', '5294329219965272288'), 'BF': ('🇧🇫', '5913407764515786948'), 'ER': ('🇪🇷', '5433723401464198287'), 'MW': ('🇲🇼', '5433968339154122439'), 'MR': ('🇲🇷', '5433859405898594234'), 'NR': ('🇳🇷', '5434131139889478358'), 'SA': ('🇸🇦', '4985897134424328239'), 'TO': ('🇹🇴', '5433640100573491806'), 'TV': ('🇹🇻', '5433684690923961019'), 'TW': ('🇹🇼', '5366187256937726720'), 'HK': ('🇭🇰', '5292166459118606932'), 'MO': ('🇲🇴', '6323557758096377611'), 'YT': ('🇾🇹', '5780471598922337683'), 'NC': ('🇳🇨', '5780471598922337683'), 'NU': ('🇳🇺', '5780471598922337683'), 'NF': ('🇳🇫', '5780471598922337683'), 'PN': ('🇵🇳', '5780471598922337683'), 'RE': ('🇷🇪', '5780471598922337683'), 'SH': ('🇸🇭', '5780471598922337683'), 'TK': ('🇹🇰', '5780471598922337683'), 'TC': ('🇹🇨', '5780471598922337683'), 'VI': ('🇻🇮', '5780471598922337683'), 'WF': ('🇼🇫', '5780471598922337683'), 'EH': ('🇪🇭', '5780471598922337683'), 'CK': ('🇨🇰', '5780471598922337683'), 'PF': ('🇵🇫', '5780471598922337683'), 'GI': ('🇬🇮', '5780471598922337683'), 'SJ': ('🇸🇯', '5780471598922337683'), 'AX': ('🇦🇽', '5780471598922337683'), 'JE': ('🇯🇪', '5780471598922337683'), 'GG': ('🇬🇬', '5780471598922337683'), 'IM': ('🇮🇲', '5226538255029121667'), 'PM': ('🇵🇲', '5780471598922337683'), 'SX': ('🇸🇽', '5461113820955027461'), 'BQ': ('🇧🇶', '5780471598922337683')}

PREMIUM_SERVICES = {'MILIMUM': ('☺️', '6260084648336957098'), 'GOLD PARI': ('🐸', '6260330402070666931'), 'LINEBET': ('👈', '6224136214451069617'), 'AZIMUTBET': ('😳', '6235684101609759140'), 'TALBAT': ('🤣', '6226499460076151578'), 'FACEBOOK': ('📱', '5323261730283863478'), 'WHATSAPP': ('📱', '5334998226636390258'), 'INSTAGRAM': ('📱', '5319160079465857105'), 'TELEGRAM': ('✈️', '5337010556253543833'), 'HSBC': ('💄', '5161519678597629383'), 'IMO': ('💭', '5337155807752524558'), 'APPLE': ('🍎', '5334637951894722661'), 'GOOGLE': ('🔍', '5335010201005231986'), 'MICROSOFT': ('🪟', '5334880948259427772'), 'TEAMS': ('🧑\u200d🤝\u200d🧑', '5334590977837403844'), 'TIKTOK': ('📱', '5327982530702359565'), 'BKASH': ('🏦', '5348469219761626211'), 'ROCKET': ('🚀', '5346042941196507141'), 'BYBIT': ('📈', '5348372939479751825'), 'BINANCE': ('💱', '5348212415077064131'), 'MELBET': ('🧡', '5287450237135246599'), 'SNAPCHAT': ('👻', '5359441366554255082'), 'UBER': ('🚗', '5298715455316303708'), 'PAYPAL': ('💵', '5776103539872896061'), 'DISCORD': ('🎬', '5116246243646898866'), 'AMAZON': ('🌟', '4995019580536524226'), 'VIBER': ('💜', '5463060437572528782'), 'LINKEDIN': ('💼', '6224222994265279792'), 'LINE': ('🔒', '5399818044866327279'), 'WECHAT': ('🌟', '5782757599560602950'), 'TWITTER': ('🐦', '5215726959056662534'), 'REDDIT': ('👽', '4992421103847604984'), 'PINTEREST': ('📌', '5346103513120258857'), 'TWITCH': ('🎮', '5233333563306301418'), 'ZOOM': ('📹', '5881799193219043268'), 'SIGNAL': ('💬', '5293998404404272267'), 'SLACK': ('💻', '4994972469040251302'), 'SKYPE': ('☎️', '4992613535562334989'), 'NETFLIX': ('🎥', '6255738712664050133'), 'SPOTIFY': ('🎵', '5411392711146095115'), 'AMAZON PRIME': ('📺', '6111801057061374810'), 'HOICHOI': ('🍿', '6104822598493801746'), 'DARAZ': ('📦', '5336879280578138635'), 'FOODPANDA': ('🐼', '5336879280578138635'), 'PATHAO': ('🛵', '5336879280578138635'), 'ALIEXPRESS': ('🛒', '5336879280578138635'), 'SHOPEE': ('🛍️', '5336879280578138635'), 'PAYONEER': ('💳', '5336879280578138635'), 'WISE': ('🦉', '5336879280578138635'), 'CHATGPT': ('🤖', '5296516998996445955'), 'NOTION': ('📓', '5336879280578138635'), 'GITHUB': ('🐙', '5417836094098007862'), 'CANVA': ('🖌️', '5111661409008092227'), 'FIGMA': ('🎨', '5336879280578138635'), 'UPWORK': ('💼', '5336879280578138635'), 'FIVERR': ('🟢', '5336879280578138635'), 'YAHOO': ('🌐', '5336879280578138635'), 'DROPBOX': ('☁️', '5336879280578138635'), 'COURSERA': ('📚', '5336879280578138635'), 'DUOLINGO': ('🗣️', '5336879280578138635'), 'QSMS': ('📱', '6321257309188136835'), 'TIK TOK': ('📱', '5327982530702359565'), 'INDRIVE': ('🌟', '6181211701409489638'), 'ALIPAY': ('😀', '6039338572161486731'), 'LILBET': ('📱', '5337132498965010628'), '1XBET': ('1️⃣', '5292091816881970192'), 'HUAWEI': ('📱', '5337132498965010628'), 'TRIP': ('📱', '5337132498965010628'), 'TOTERS': ('😉', '6204111865736340573'), 'TINDER': ('📱', '5969908145194015215'), 'CO STAR': ('🚀', '5195033767969839232'), 'SWITCH': ('😘', '6206065749438505333'), 'BOTONGAME': ('😁', '6213223144933563831')}

PREMIUM_FLAGS["MM"] = ("🇲🇲", "5294254478944393569")
PREMIUM_SERVICES.update({
    "MILIMUM": ("☺️", "6260084648336957098"), "GOLD PARI": ("🐸", "6260330402070666931"),
    "LINEBET": ("👈", "6224136214451069617"), "AZIMUTBET": ("😳", "6235684101609759140"),
    "TALBAT": ("🤣", "6226499460076151578"), "1XBET": ("1️⃣", "5292091816881970192"),
    "MELBET": ("🧡", "5287450237135246599"), "FACEBOOK": ("📱", "5323261730283863478"),
    "INSTAGRAM": ("📱", "5319160079465857105"), "TIK TOK": ("📱", "5327982530702359565"),
    "TIKTOK": ("📱", "5327982530702359565"), "WHATSAPP": ("📱", "5334998226636390258"),
})
_PREM_SVC_NORM = sorted(((k.replace(" ", ""), k) for k in PREMIUM_SERVICES), key=lambda x: -len(x[0]))

LANG_CODE = {
    "English": "EN", "Spanish": "ES", "Portuguese": "PT", "French": "FR", "German": "DE",
    "Russian": "RU", "Ukrainian": "UK", "Polish": "PL", "Romanian": "RO", "Chinese": "ZH",
    "Japanese": "JA", "Korean": "KO", "Arabic": "AR", "Hindi": "HI", "Nepali": "NE",
    "Bengali": "BN", "Urdu": "UR", "Sinhala": "SI", "Burmese": "MY", "Thai": "TH",
    "Vietnamese": "VI", "Khmer": "KM", "Indonesian": "ID", "Malay": "MS", "Filipino": "FIL",
    "Turkish": "TR", "Azerbaijani": "AZ", "Uzbek": "UZ", "Turkmen": "TK", "Kyrgyz": "KY",
    "Tajik": "TG", "Armenian": "HY", "Georgian": "KA", "Mongolian": "MN", "Persian": "FA",
    "Dari": "PRS", "Hebrew": "HE", "Amharic": "AM",
}

def _emo(emoji, eid):
    return f'<tg-emoji emoji-id="{eid}">{emoji}</tg-emoji>'

# ===================== SERVICE DETECT =====================
def detect_service(msg):
    msg_upper = msg.upper()
    if any(k in msg_upper for k in ["FACEBOOK", "FB"]):
        return "FACEBOOK"
    if any(k in msg_upper for k in ["INSTAGRAM", "IG", "INSTA"]):
        return "INSTAGRAM"
    if any(k in msg_upper for k in ["WHATSAPP", "WA"]):
        return "WHATSAPP"
    if "TELEGRAM" in msg_upper:
        return "TELEGRAM"
    squeezed = msg_upper.replace(" ", "")
    for norm, name in _PREM_SVC_NORM:
        if norm in squeezed:
            return name
    return "OTP"

# ===================== OTP EXTRACT =====================
def extract_otp(message_text, phone_number=None):
    if not message_text:
        return None
    phone_digits = re.sub(r'\D', '', str(phone_number)) if phone_number else ""
    spaced = re.findall(r'\b(\d[\d ]{2,12}\d)\b', message_text)
    for match in spaced:
        joined = match.replace(" ", "")
        if not joined.isdigit():
            continue
        if phone_digits and (joined in phone_digits or phone_digits in joined):
            continue
        if 4 <= len(joined) <= 8:
            return joined
    candidates = re.findall(r'\b(\d{4,8})\b', message_text)
    for candidate in candidates:
        if phone_digits:
            if candidate in phone_digits:
                continue
            if phone_digits.endswith(candidate):
                continue
            if phone_digits[-8:] == candidate:
                continue
        if 4 <= len(candidate) <= 8:
            return candidate
    return None

# ===================== AUTO DELETE =====================
def auto_delete(chat_id, message_id, delay=AUTO_DELETE_SEC):
    """delay সেকেন্ড পর মেসেজ ডিলিট করবে"""
    def _delete():
        time.sleep(delay)
        try:
            url = f"https://api.telegram.org/bot{BOT_TOKEN}/deleteMessage"
            HTTP.post(url, json={
                "chat_id": chat_id,
                "message_id": message_id
            }, timeout=10)
        except Exception as e:
            print(f"[Delete Error] {e}")
    threading.Thread(target=_delete, daemon=True).start()

# ===================== Console API =====================
def get_country_info(number):
    try:
        clean_number = re.sub(r'\D', '', str(number))
        parsed_number = phonenumbers.parse("+" + clean_number, None)
        country_name = geocoder.country_name_for_number(parsed_number, "en")
        alpha2 = get_alpha2(country_name)
        flag   = get_flag(country_name)
        short  = get_short_code(country_name)
        lang   = get_language(alpha2)
        return flag, short, lang, country_name if country_name else "Unknown"
    except Exception:
        return "🌐", "#??", "English", "Unknown"

def build_message(masked_number, flag, short_code, service, lang):
    """
    ╭───────🫀───────╮
    │ 🇨🇲 CM  🧩 +2376🟢01564  EN  │
    ╰───────🐋───────╯
    """
    iso = short_code.replace("#", "").strip().upper()
    if iso in PREMIUM_FLAGS:
        pf, pid = PREMIUM_FLAGS[iso]
        flag_html = _emo(pf, pid)
    else:
        flag_html = _html.escape(flag)
    svc = PREMIUM_SERVICES.get(str(service).upper())
    svc_html = _emo(svc[0], svc[1]) if svc else "🧩"
    lang_code = LANG_CODE.get(lang, str(lang)[:2].upper())
    return (
        f"<b>╭───────{_emo('🫀', '5116512467194741904')}───────╮\n"
        f"│ {flag_html} {_html.escape(iso)}  {svc_html} {masked_number}  {lang_code}  │\n"
        f"╰───────{_emo('🐋', '5084613633418199991')}───────╯</b>"
    )

RANGE_CHANNEL_URL = "https://t.me/range_channele"
PANEL_BOT_URL     = "https://t.me/shuvo_number_bot"

# ===================== SEND WITH STYLED BUTTONS =====================
def send_with_styled_buttons(text, otp_code, full_message, range_clean):
    """
    বাটন:
    🟢 OTP কোড (সবুজ)  | 🔴 Full Message (লাল)
    🔵 NUMBER BOT       | 🔵 METHOD
    """
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHANNEL_ID,
        "text": text,
        "parse_mode": "HTML",
        "reply_markup": {
            "inline_keyboard": [
                [
                    {
                        "text": f"{otp_code}",
                        "copy_text": {"text": otp_code},
                        "style": "success"
                    },
                    {
                        "text": "Full Message",
                        "copy_text": {"text": full_message},
                        "style": "danger"
                    }
                ],
                [
                    {
                        "text": "𝙽𝚄𝙼𝙱𝙴𝚁 𝙱𝙾𝚃",
                        "url": PANEL_BOT_URL,
                        "style": "primary"
                    },
                    {
                        "text": "𝙼𝙴𝚃𝙷𝙾𝙳",
                        "url": RANGE_CHANNEL_URL,
                        "style": "primary"
                    }
                ]
            ]
        }
    }
    try:
        res = HTTP.post(url, json=payload, timeout=10)
        result = res.json()
        if res.status_code == 429:
            time.sleep(min(int(result.get("parameters", {}).get("retry_after", 2)), 30))
            res = HTTP.post(url, json=payload, timeout=10)
            result = res.json()
        if result.get("ok"):
            message_id = result["result"]["message_id"]
            auto_delete(CHANNEL_ID, message_id, AUTO_DELETE_SEC)
        else:
            # Fallback
            fallback_markup = types.InlineKeyboardMarkup()
            fallback_markup.row(
                types.InlineKeyboardButton(
                    text=f"{otp_code}",
                    copy_text=types.CopyTextButton(text=otp_code)
                ),
                types.InlineKeyboardButton(
                    text="Full Message",
                    copy_text=types.CopyTextButton(text=full_message)
                )
            )
            fallback_markup.row(
                types.InlineKeyboardButton("𝙽𝚄𝙼𝙱𝙴𝚁 𝙱𝙾𝚃", url=PANEL_BOT_URL),
                types.InlineKeyboardButton("𝙼𝙴𝚃𝙷𝙾𝙳", url=RANGE_CHANNEL_URL)
            )
            sent = bot.send_message(CHANNEL_ID, text, reply_markup=fallback_markup, parse_mode="HTML")
            auto_delete(CHANNEL_ID, sent.message_id, AUTO_DELETE_SEC)
    except Exception as e:
        print(f"[Send Error] {e}")

def fill_xxx(number_str):
    def replace_x(match):
        return ''.join([str(random.randint(0, 9)) for _ in match.group()])
    filled = re.sub(r'[Xx]+', replace_x, number_str)
    return re.sub(r'\D', '', filled)

def mask_number(number_str):
    """
    নাম্বার format: দেশ কোড + 𝘚𝘩𝘶𝘷𝘰 + শেষের কিছু ডিজিট
    মোট দৈর্ঘ্য সর্বোচ্চ ৫ ডিজিট দেখাবে (দেশ কোড + ৩ শেষ)
    উদাহরণ: 2557382345 → 255𝘚𝘩𝘶𝘷𝘰345
    উদাহরণ: 22465451630 → 224𝘚𝘩𝘶𝘷𝘰630
    """
    digits = re.sub(r'\D', '', number_str)
    MASK = _emo('🟢', '5208575460551710333')
    if len(digits) <= 3:
        return "+" + digits + MASK
    # দেশ কোড = প্রথম ১-৩ ডিজিট (সর্বোচ্চ ৩)
    prefix = digits[:3]
    suffix = digits[-3:]
    return f"+{prefix}{MASK}{suffix}"

def send_styled_otp(hit):
    otp_full    = hit.get("message", "")
    full_number = str(hit.get("range", ""))

    flag, short_code, lang, country = get_country_info(full_number)

    real_num    = re.sub(r'[Xx]', '', full_number)
    real_digits = re.sub(r'\D', '', real_num)
    filled_num  = fill_xxx(full_number)
    masked      = mask_number(filled_num)   # 255𝘚𝘩𝘶𝘷𝘰538

    otp_code = extract_otp(otp_full, full_number)
    if not otp_code:
        m = re.search(r'\b\d{5,8}\b', otp_full)
        otp_code = m.group() if m else re.sub(r'\D', '', otp_full)[:8] or "------"

    service      = detect_service(otp_full)
    text         = build_message(masked, flag, short_code, service, lang)
    full_message = otp_full  # Full Message বাটনে পুরো message কপি হবে

    send_with_styled_buttons(text, otp_code, full_message, real_digits)

# ===================== NEXUS OTP HANDLER =====================
def send_nexus_otp(api_id, number, otp_data):
    """NEXUS থেকে OTP পেলে channel এ পাঠাব"""
    try:
        flag, short_code, lang, country = get_country_info(number)

        real_digits = re.sub(r'\D', '', str(number))
        masked      = mask_number(real_digits)   # 255𝘚𝘩𝘶𝘷𝘰538

        otp_body = (
            otp_data.get("text") or
            otp_data.get("body") or
            otp_data.get("message") or ""
        )
        otp_code = extract_otp(otp_body, number)
        if not otp_code:
            otp_code = re.sub(r'\D', '', otp_body)[:8] or "------"

        service      = detect_service(otp_body)
        text         = build_message(masked, flag, short_code, service, lang)
        full_message = otp_body

        send_with_styled_buttons(text, otp_code, full_message, real_digits)
        print(f"✅ NEXUS OTP sent: {api_id} -> {otp_code}")
    except Exception as e:
        print(f"[NEXUS Error] {e}")

def check_nexus_otp():
    """NEXUS API থেকে OTP check করছি"""
    try:
        history = pickle.load(open(NEXUS_DB_FILE, "rb")) if os.path.exists(NEXUS_DB_FILE) else {}
        
        for api_id, number in NEXUS_TRACKING.items():
            try:
                r = HTTP.get(
                    f"{NEXUS_BASE_URL}/numbers/{api_id}",
                    headers=NEXUS_HEADERS,
                    timeout=15
                )
                
                if r.status_code == 200:
                    data = r.json()
                    
                    if data.get("ok") and data.get("otps"):
                        for otp_item in data.get("otps", []):
                            otp_id = otp_item.get("id")
                            
                            if otp_id and otp_id not in history:
                                send_nexus_otp(api_id, number, otp_item)
                                history[otp_id] = True
                                time.sleep(1)
                
            except Exception as e:
                print(f"[NEXUS Check Error] {e}")
        
        # Save history
        pickle.dump(history, open(NEXUS_DB_FILE, "wb"))
    except Exception as e:
        print(f"[NEXUS History Error] {e}")

def run_bot():
    print("🚀 OTP Bot (STEX + NEXUS) started...")
    while True:
        try:
            # STEX Console API check করছি
            res = HTTP.get(CONSOLE_URL, headers=HEADERS, timeout=10).json()
            if res.get("meta", {}).get("status") == "ok":
                history = pickle.load(open(DB_FILE, "rb")) if os.path.exists(DB_FILE) else {}
                for hit in res.get("data", {}).get("hits", []):
                    msg_time = str(hit.get("time", ""))
                    if msg_time not in history:
                        send_styled_otp(hit)
                        history[msg_time] = True
                        pickle.dump(history, open(DB_FILE, "wb"))
                        time.sleep(1.0)
        except Exception as e:
            print(f"[STEX Error] {e}")
        
        # NEXUS check করছি
        try:
            check_nexus_otp()
        except Exception as e:
            print(f"[NEXUS Polling Error] {e}")
        
        time.sleep(3)

# ===================== MAIN =====================
if __name__ == "__main__":
    keep_alive()
    threading.Thread(target=run_bot, daemon=True).start()
    print("✅ NEXUS + STEX OTP Bot running!")
    while True:
        time.sleep(60)
