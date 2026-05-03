import os, platform, sys

# আর্কিটেকচার চেক (৬৪ বিট ছাড়া চলবে না)
def check_arch():
    if "aarch64" not in platform.machine().lower():
        print("\033[1;31m❌ SORRY! YOUR DEVICE IS 32-BIT."); sys.exit()

try:
    import HBXUSER, telebot
    check_arch()
    os.system("clear")
    HBXUSER.professional_logo() # আপনার লোগো দেখাবে
    
    print("\033[1;37m--------------------------------------------")
    token = input("\033[1;36m[?] BOT TOKEN DAW MAMA: \033[0m")
    print("\033[1;37m--------------------------------------------")
    
    if ":" not in token:
        print("\033[1;31m[!] INVALID TOKEN!"); sys.exit()

    print("\n\033[1;32m[+] BOT CONNECTING...")
    bot = telebot.TeleBot(token)
    bot.infinity_polling()

except ImportError:
    print("\033[1;31m❌ Error: HBXUSER.so or telebot library missing!")
except Exception as e:
    print(f"Error: {e}")