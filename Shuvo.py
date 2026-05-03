import os
import sys
import time
from colorama import Fore, Style, init

# কালার সেটিংস ঠিক করা
init(autoreset=True)

def my_banner():
    # স্ক্রিন পরিষ্কার করা
    os.system('clear')

    # আপনার নামের ASCII Art (বড় করে নাম দেখানো)
    print(f"{Fore.CYAN}{Style.BRIGHT}")
    print("  ____  _   _ _   ____     _____ ")
    print(" / ___|| | | | | | \ \   / / _ \ ")
    print(" \___ \| |_| | | | |\ \ / / | | |")
    print("  ___) |  _  | |_| | \ V /| |_| |")
    print(" |____/|_| |_|\___/   \_/  \___/ ")
    
    print(f"{Fore.WHITE}--------------------------------------------------")
    
    # আপনার ব্যক্তিগত তথ্য
    print(f"{Fore.GREEN}[S] {Fore.YELLOW}DEVELOPER : SHUVO")
    print(f"{Fore.GREEN}[O] {Fore.YELLOW}TEAM      : TEAM WITH SHUVO")
    print(f"{Fore.GREEN}[K] {Fore.YELLOW}TOOLS     : SHUVO ULTRA SPEED BOT")
    print(f"{Fore.GREEN}[Y] {Fore.YELLOW}VERSION   : (v1.0)")
    
    print(f"{Fore.WHITE}--------------------------------------------------")
    print(f"{Fore.YELLOW}      [#]--- TEAM WITH SHUVO USER ---[#]")
    print(f"{Fore.WHITE}--------------------------------------------------")
    
    print(f"\n{Fore.GREEN}[+] SHUVO TMUSER বট রান হচ্ছে...")
    
    # নিচের লাইনগুলো ছবির মতো দেখাবে
    print(f"{Fore.WHITE}cd SHUVO-UPDATE-COOKIES")
    print(f"{Fore.WHITE}python Shuvo.py")
    print(f"{Fore.WHITE}" + "-" * 15)

# ব্যানারটি দেখানোর জন্য ফাংশন কল করা
my_banner()

# --- এর নিচে আপনার বটের আসল কাজ বা লজিক শুরু হবে ---
# উদাহরণস্বরূপ:
print(f"{Fore.CYAN}বট কানেক্ট হচ্ছে... দয়া করে অপেক্ষা করুন।")

# আপনি যদি টেলিগ্রাম বটের কাজ করতে চান, তবে এখানে আপনার টোকেন এবং লজিক বসাবেন।