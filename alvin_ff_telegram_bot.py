#!/usr/bin/env python3
"""
ALVIN FF CHECKER - TELEGRAM BOT VERSION v2.0
Features:
- /start <threads> <mode> <letters>  - Start generator
- /stop                               - Stop generator
- /log                                - Show stats/log
- Auto-send JSON batch every 10 rare accounts (same 5-9)
- Real-time notifications for rare finds
"""

import warnings
warnings.filterwarnings('ignore')
import requests
import random
import string
import time
import os
import json
import codecs
import base64
import sys
import hashlib
import secrets
import re
import threading
import tempfile
import shutil
import asyncio
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import deque, Counter
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ═══════════════════════════════════════════
# TELEGRAM BOT CONFIG
# ═══════════════════════════════════════════
BOT_TOKEN = "8885313876:AAF2n49W-75C1Jk1WANtj1jwyA-l-WpHDis"
CHAT_ID = "8818676309"
TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}"

# ═══════════════════════════════════════════
# API & PATHS
# ═══════════════════════════════════════════
API_BASE = "https://api.gameskinbo.com"
API_CHECK = f"{API_BASE}/api/check"
API_CHECK_TRIAL = f"{API_BASE}/api/check_trial"
API_STATUS = f"{API_BASE}/api/status"
API_VERSION = f"{API_BASE}/version.json"

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if not CURRENT_DIR or CURRENT_DIR == os.getcwd():
    CURRENT_DIR = os.getcwd()
CHATGPT_DIR = os.path.join(CURRENT_DIR, ".alvin_config")
os.makedirs(CHATGPT_DIR, exist_ok=True)

USER_KEY_FILE = os.path.join(CHATGPT_DIR, ".alvinfk_userkey")
DEVICE_FILE = os.path.join(CHATGPT_DIR, ".device_id")
TRIAL_KEY_FILE = os.path.join(CHATGPT_DIR, ".trial_key")
LICENSE_INFO_FILE = os.path.join(CHATGPT_DIR, ".license_info")
OUTPUT_MODE_FILE = os.path.join(CHATGPT_DIR, ".output_mode")
CUSTOM_NAME_FILE = os.path.join(CHATGPT_DIR, ".custom_name")
RARE_ONLY_FILE = os.path.join(CHATGPT_DIR, ".rare_only")
CUSTOM_LETTERS_FILE = os.path.join(CHATGPT_DIR, ".custom_letters")

OUTPUT_FOLDER = os.path.join(CURRENT_DIR, "ALVIN_FF")
SPECIAL_FOLDER = os.path.join(OUTPUT_FOLDER, "special")
ALL_FOLDER = os.path.join(OUTPUT_FOLDER, "allaccount")
os.makedirs(SPECIAL_FOLDER, exist_ok=True)
os.makedirs(ALL_FOLDER, exist_ok=True)

REGION = "ID"
REGION_NAME = "ID"
REGION_LANG = {"ID": "id"}

# Region rotation
REGION_POOL = ["TH", "ME", "BR", "VN", "PH", "SG", "MY", "MX"]
region_index = 0
REGION_LOCK = threading.Lock()

def get_next_region():
    global region_index
    with REGION_LOCK:
        region_index = (region_index + 1) % len(REGION_POOL)
        return REGION_POOL[region_index]

THREAD_COUNT = 20
FAIL_SLEEP = 0

WATERMARK = "ALVIN FF TEAM"
CHANNEL_LINK = "https://whatsapp.com/channel/0029Vb8wnA5LdQek3w0nUw1S"
VERSION = "v2.0.0-TELEGRAM"
DEV_NAME = "Alvin"

last_success_time = time.time()
stuck_warning_shown = False
file_lock = threading.RLock()
session_pool = deque()
session_lock = threading.Lock()
running = False
target_mode_active = False
target_id = None
target_progress = 0
rare_only = False

stats = {
    'total': 0, 'same_5': 0, 'same_6': 0,
    'same_7': 0, 'same_8': 0, 'same_9': 0,
    'same_10': 0, 'same_11plus': 0, 'start_time': time.time()
}
stats_lock = threading.Lock()
stuck_monitor_active = True

# Batch queue for Telegram
batch_queue = []
batch_lock = threading.Lock()
BATCH_SIZE = 10

class C:
    RESET = '\033[0m'
    BOLD = '\033[1m'
    BLINK = '\033[5m'
    BG_RED = '\033[41m'
    BG_GREEN = '\033[42m'
    BG_YELLOW = '\033[43m'
    BG_BLUE = '\033[44m'
    BG_MAGENTA = '\033[45m'
    BG_TOSCA = '\033[46m'
    BG_WHITE = '\033[47m'
    BG_BRIGHT_RED = '\033[101m'
    BG_BRIGHT_GREEN = '\033[102m'
    BG_BRIGHT_YELLOW = '\033[103m'
    BG_BRIGHT_BLUE = '\033[104m'
    BG_BRIGHT_MAGENTA = '\033[105m'
    BG_BRIGHT_CYAN = '\033[106m'
    BG_BRIGHT_WHITE = '\033[107m'
    BLACK = '\033[30m'
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN = '\033[36m'
    WHITE = '\033[37m'
    BRIGHT_WHITE = '\033[97m'
    DIM = '\033[2m'

# ═══════════════════════════════════════════
# TELEGRAM FUNCTIONS
# ═══════════════════════════════════════════

def send_telegram_message(text, parse_mode="HTML"):
    """Send text message to Telegram"""
    try:
        url = f"{TELEGRAM_API}/sendMessage"
        payload = {
            "chat_id": CHAT_ID,
            "text": text,
            "parse_mode": parse_mode,
            "disable_web_page_preview": True
        }
        resp = requests.post(url, json=payload, timeout=10)
        return resp.status_code == 200
    except Exception as e:
        print(f"[TELEGRAM] Error sending message: {e}")
        return False

def send_telegram_document(file_path, caption=""):
    """Send document/file to Telegram"""
    try:
        url = f"{TELEGRAM_API}/sendDocument"
        with open(file_path, 'rb') as f:
            files = {'document': f}
            data = {'chat_id': CHAT_ID, 'caption': caption, 'parse_mode': 'HTML'}
            resp = requests.post(url, files=files, data=data, timeout=30)
        return resp.status_code == 200
    except Exception as e:
        print(f"[TELEGRAM] Error sending document: {e}")
        return False

def send_telegram_json(data_list, caption=""):
    """Send JSON data as formatted message"""
    try:
        json_str = json.dumps(data_list, indent=2, ensure_ascii=False)
        # If too long, send as file
        if len(json_str) > 4000:
            temp_file = os.path.join(tempfile.gettempdir(), f"alvin_batch_{int(time.time())}.json")
            with open(temp_file, 'w', encoding='utf-8') as f:
                f.write(json_str)
            result = send_telegram_document(temp_file, caption)
            try:
                os.remove(temp_file)
            except:
                pass
            return result
        else:
            text = f"{caption}\n\n<pre>{json_str}</pre>"
            return send_telegram_message(text)
    except Exception as e:
        print(f"[TELEGRAM] Error sending JSON: {e}")
        return False

def send_rare_notification(account_data):
    """Send instant notification for rare account"""
    same_count = account_data.get('same_digit_count', 0)
    most_digit = account_data.get('most_digit', '')
    uid = account_data.get('uid', 'N/A')
    aid = account_data.get('account_id', 'N/A')
    password = account_data.get('password', 'N/A')
    name = account_data.get('name', 'N/A')

    rarity_emoji = "🔥" if same_count >= 9 else "⚡" if same_count >= 7 else "💎"

    text = f"""{rarity_emoji} <b>RARE ACCOUNT FOUND!</b> {rarity_emoji}

<b>Account ID:</b> <code>{aid}</code>
<b>UID:</b> <code>{uid}</code>
<b>Password:</b> <code>{password}</code>
<b>Name:</b> {name}
<b>Same Digits:</b> {most_digit}x{same_count}
<b>Rarity:</b> {get_rarity_name(same_count)}
<b>Time:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

🤖 <i>ALVIN FF Bot</i>"""

    send_telegram_message(text)

def get_rarity_name(same_count):
    if same_count >= 9:
        return "GODLIKE"
    elif same_count == 8:
        return "MYTHIC"
    elif same_count == 7:
        return "LEGENDARY"
    elif same_count == 6:
        return "EPIC"
    elif same_count == 5:
        return "RARE"
    elif same_count == 4:
        return "UNCOMMON"
    else:
        return "COMMON"

# ═══════════════════════════════════════════
# PROXY AUTO-LOADER
# ═══════════════════════════════════════════

def load_proxies_from_file():
    proxy_file = os.path.join(CURRENT_DIR, "proxy.txt")
    proxies = [None]
    if os.path.exists(proxy_file):
        try:
            with open(proxy_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        if not line.startswith('http'):
                            line = f"http://{line}"
                        proxies.append(line)
            print(f"{C.GREEN}✓ Loaded {len(proxies)-1} proxies from proxy.txt{C.RESET}")
        except Exception as e:
            print(f"{C.YELLOW}⚠ Error loading proxy.txt: {e}{C.RESET}")
    else:
        print(f"{C.YELLOW}⚠ No proxy.txt found - create one with ip:port per line{C.RESET}")
    return proxies

PROXY_LIST = [None]
proxy_index = 0
PROXY_LOCK = threading.Lock()

def get_next_proxy():
    global proxy_index
    with PROXY_LOCK:
        if len(PROXY_LIST) <= 1:
            return None
        proxy = PROXY_LIST[proxy_index % len(PROXY_LIST)]
        proxy_index += 1
        return proxy

# ═══════════════════════════════════════════
# CHARACTER SETS
# ═══════════════════════════════════════════

VIETNAMESE_LETTERS = [
    'a','à','á','ả','ã','ạ','ă','ằ','ắ','ẳ','ẵ','ặ','â','ầ','ấ','ẩ','ẫ','ậ',
    'b','c','d','đ','e','è','é','ẻ','ẽ','ẹ','ê','ề','ế','ể','ễ','ệ',
    'g','h','i','ì','í','ỉ','ĩ','ị','k','l','m','n',
    'o','ò','ó','ỏ','õ','ọ','ô','ồ','ố','ổ','ỗ','ộ','ơ','ờ','ớ','ở','ỡ','ợ',
    'p','q','r','s','t','u','ù','ú','ủ','ũ','ụ','ư','ừ','ứ','ử','ữ','ự',
    'v','x','y','ỳ','ý','ỷ','ỹ','ỵ',
    'A','À','Á','Ả','Ã','Ạ','Ă','Ằ','Ắ','Ẳ','Ẵ','Ặ','Â','Ầ','Ấ','Ẩ','Ẫ','Ậ',
    'B','C','D','Đ','E','È','É','Ẻ','Ẽ','Ẹ','Ê','Ề','Ế','Ể','Ễ','Ệ',
    'G','H','I','Ì','Í','Ỉ','Ĩ','Ị','K','L','M','N',
    'O','Ò','Ó','Ỏ','Õ','Ọ','Ô','Ồ','Ố','Ổ','Ỗ','Ộ','Ơ','Ờ','Ớ','Ở','Ỡ','Ợ',
    'P','Q','R','S','T','U','Ù','Ú','Ủ','Ũ','Ụ','Ư','Ừ','Ứ','Ử','Ữ','Ự',
    'V','X','Y','Ỳ','Ý','Ỷ','Ỹ','Ỵ'
]

KHMER_LETTERS = [
    'ក','ខ','គ','ឃ','ង','ច','ឆ','ជ','ឈ','ញ','ដ','ឋ','ឌ','ឍ','ណ','ត',
    'ថ','ទ','ធ','ន','ប','ផ','ព','ភ','ម','យ','រ','ល','វ','ឝ','ឞ','ស',
    'ហ','ឡ','អ','ឣ','ឤ','ឥ','ឦ','ឧ','ឨ','ឩ','ឪ','ឫ','ឬ','ឭ','ឮ','ឯ',
    'ឰ','ឱ','ឲ','ឳ','កា','ខា','គា','ឃា','ងា','ចា','ឆា','ជា','ឈា','ញា',
    'ដា','ឋា','ឌា','ឍា','ណា','តា','ថា','ទា','ធា','នា','បា','ផា','ពា',
    'ភា','មា','យា','រា','លា','វា','សា','ហា','ឡា','អា'
]

THAI_LETTERS = [
    'ก','ข','ฃ','ค','ฅ','ฆ','ง','จ','ฉ','ช','ซ','ฌ','ญ','ฎ','ฏ','ฐ','ฑ','ฒ',
    'ณ','ด','ต','ถ','ท','ธ','น','บ','ป','ผ','ฝ','พ','ฟ','ภ','ม','ย','ร','ฤ',
    'ล','ว','ศ','ษ','ส','ห','ฬ','อ','ฮ',
    'ะ','ั','า','ำ','ิ','ี','ึ','ื','ุ','ู','เ','แ','โ','ใ','ไ','ๅ','ๆ','็',
    '่','้','๊','๋','์','ํ','ฺ','฿','ฯ','๏','๚','๛'
]

JAPANESE_LETTERS = [
    'あ','い','う','え','お','か','き','く','け','こ','さ','し','す','せ','そ',
    'た','ち','つ','て','と','な','に','ぬ','ね','の','は','ひ','ふ','へ','ほ',
    'ま','み','む','め','も','や','ゆ','よ','ら','り','る','れ','ろ','わ','を','ん',
    'ぁ','ぃ','ぅ','ぇ','ぉ','っ','ゃ','ゅ','ょ',
    'ア','イ','ウ','エ','オ','カ','キ','ク','ケ','コ','サ','シ','ス','セ','ソ',
    'タ','チ','ツ','テ','ト','ナ','ニ','ヌ','ネ','ノ','ハ','ヒ','フ','ヘ','ホ',
    'マ','ミ','ム','メ','モ','ヤ','ユ','ヨ','ラ','リ','ル','レ','ロ','ワ','ヲ','ン',
    'ァ','ィ','ゥ','ェ','ォ','ッ','ャ','ュ','ョ'
]

MANDARIN_LETTERS = [
    '的','一','是','了','我','不','人','在','他','有','这','个','上','们','来',
    '到','时','大','地','为','子','中','你','说','生','国','年','着','就','那',
    '和','要','她','出','也','得','里','后','自','以','会','家','可','下','而',
    '过','天','去','能','对','小','多','然','于','心','学','么','之','都','好',
    '看','起','发','当','没','成','只','如','事','把','还','用','第','样','道',
    '想','作','种','开','手','爱','情','王','龙','虎','凤','皇','帝','君','子',
    '文','武','神','仙','魔','鬼','妖','灵','圣','贤','义','勇','忠','诚','信'
]

CHARS = VIETNAMESE_LETTERS + KHMER_LETTERS + THAI_LETTERS + JAPANESE_LETTERS + MANDARIN_LETTERS

# ═══════════════════════════════════════════
# DEVICE POOL
# ═══════════════════════════════════════════

DEVICE_POOL = []
samsung = [f"SM-{c}{random.randint(100,999)}" for _ in range(2000) for c in "AGNFMSJE"]
xiaomi = [f"{p} {random.randint(7,14)}" for _ in range(1500) for p in ["Redmi Note", "Redmi", "Poco F", "Poco X", "Mi", "Xiaomi", "Redmi K", "Poco M"]]
oppo = [f"OPPO {m}{random.randint(2,9999)}" for _ in range(1200) for m in ["CPH", "Find X", "Reno", "A", "F", "R", "K"]]
vivo = [f"vivo {m}{random.randint(1,9999)}" for _ in range(1200) for m in ["V", "X", "Y", "T", "S", "U", "Z"]]
realme = [f"Realme {m}{random.randint(7,70)}" for _ in range(1000) for m in ["", " Pro", " GT ", " C", " Narzo ", " X", " U"]]
oneplus = [f"OnePlus {random.randint(8,14)}" for _ in range(800)]
moto = [f"Moto {m}{random.randint(10,100)}" for _ in range(800) for m in ["G", "E", "Edge ", "Z", "X"]]
google = [f"Pixel {random.randint(3,8)}" for _ in range(500)]
sony = [f"Xperia {random.randint(1,5)} {chr(65+random.randint(0,2))}" for _ in range(400)]
nokia = [f"Nokia {random.randint(1,9)}.{random.randint(1,3)}" for _ in range(300)]
lg = [f"LG {chr(65+random.randint(0,15))}{random.randint(10,99)}" for _ in range(300)]
honor = [f"Honor {random.randint(10,70)}" for _ in range(300)]
asus = [f"ASUS Zenfone {random.randint(5,10)}" for _ in range(300)]
other = ["ASUS_I005DA","ASUS ROG Phone 5","Nothing Phone 1","Nothing Phone 2","SHARP AQUOS R8","Motorola Edge","Nubia RedMagic","Black Shark","Realme GT","Poco F4","iQOO 9","Oppo Find N","Vivo X Fold"] * 200

all_models = samsung + xiaomi + oppo + vivo + realme + oneplus + moto + google + sony + nokia + lg + honor + asus + other
brands = ["samsung","xiaomi","oppo","vivo","realme","oneplus","motorola","asus","google","sony","nokia","lg","honor","poco","iqoo","nubia","blackshark","nothing"]
android_versions = ["9","10","11","12","13","14","15","16"]

for _ in range(50000):
    DEVICE_POOL.append({
        "model": random.choice(all_models),
        "brand": random.choice(brands),
        "android": random.choice(android_versions)
    })

HEX_KEY = bytes.fromhex("32656534343831396539623435393838343531343130363762323831363231383734643064356437616639643866376530306331653534373135623764316533")

# ═══════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════

def get_random_ip():
    return f"{random.randint(1,255)}.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,255)}"

def get_headers():
    device = random.choice(DEVICE_POOL)
    return {
        "User-Agent": f"GarenaMSDK/4.0.39({device['model']};Android {device['android']};en;ID;)",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Accept-Encoding": "gzip",
        "Connection": "Keep-Alive",
        "X-Unity-Version": "2018.4.11f1",
        "X-GA": f"v1 {random.randint(100000, 999999)}",
        "X-Forwarded-For": get_random_ip(),
        "X-Real-IP": get_random_ip(),
    }

def get_headers_form():
    h = get_headers()
    h["Content-Type"] = "application/x-www-form-urlencoded"
    return h

def encode_varint(n):
    if n < 0:
        return b''
    result = []
    while True:
        byte = n & 0x7F
        n >>= 7
        if n:
            byte |= 0x80
        result.append(byte)
        if not n:
            break
    return bytes(result)

def create_proto_field(field_num, value):
    if isinstance(value, dict):
        nested = b''
        for k, v in value.items():
            nested += create_proto_field(k, v)
        header = (field_num << 3) | 2
        return encode_varint(header) + encode_varint(len(nested)) + nested
    elif isinstance(value, int):
        header = (field_num << 3) | 0
        return encode_varint(header) + encode_varint(value)
    elif isinstance(value, (str, bytes)):
        encoded_val = value.encode() if isinstance(value, str) else value
        header = (field_num << 3) | 2
        return encode_varint(header) + encode_varint(len(encoded_val)) + encoded_val
    return b''

def build_proto(fields):
    return b''.join(create_proto_field(k, v) for k, v in fields.items())

def aes_encrypt(hex_data):
    from Crypto.Cipher import AES
    from Crypto.Util.Padding import pad
    data = bytes.fromhex(hex_data)
    aes_key = bytes([89, 103, 38, 116, 99, 37, 68, 69, 117, 104, 54, 37, 90, 99, 94, 56])
    iv = bytes([54, 111, 121, 90, 68, 114, 50, 50, 69, 51, 121, 99, 104, 106, 77, 37])
    cipher = AES.new(aes_key, AES.MODE_CBC, iv)
    return cipher.encrypt(pad(data, AES.block_size))

def encrypt_api(plain_hex):
    from Crypto.Cipher import AES
    from Crypto.Util.Padding import pad
    plain = bytes.fromhex(plain_hex)
    aes_key = bytes([89, 103, 38, 116, 99, 37, 68, 69, 117, 104, 54, 37, 90, 99, 94, 56])
    iv = bytes([54, 111, 121, 90, 68, 114, 50, 50, 69, 51, 121, 99, 104, 106, 77, 37])
    cipher = AES.new(aes_key, AES.MODE_CBC, iv)
    return cipher.encrypt(pad(plain, AES.block_size)).hex()

def major_login(uid, password, access_token, open_id, region):
    try:
        lang = REGION_LANG.get(region, "en")
        payload_parts = [
            b'\x1a\x132025-08-30 05:19:21"\tfree fire(\x01:\x081.114.13B2Android OS 9 / API-28 (PI/rel.cjw.20220518.114133)J\x08HandheldR\nATM MobilsZ\x04WIFI`\xb6\nh\xee\x05r\x03300z\x1fARMv7 VFPv3 NEON VMH | 2400 | 2\x80\x01\xc9\x0f\x8a\x01\x0fAdreno (TM) 640\x92\x01\rOpenGL ES 3.2\x9a\x01+Google|dfa4ab4b-9dc4-454e-8065-e70c733fa53f\xa2\x01\x0e105.235.139.91\xaa\x01\x02',
            lang.encode("ascii"),
            b'\xb2\x01 1d8ec0240ede109973f3321b9354b44d\xba\x01\x014\xc2\x01\x08Handheld\xca\x01\x10Asus ASUS_I005DA\xea\x01@afcfbf13334be42036e4f742c80b956344bed760ac91b3aff9b607a610ab4390\xf0\x01\x01\xca\x02\nATM Mobils\xd2\x02\x04WIFI\xca\x03 7428b253defc164018c604a1ebbfebdf\xe0\x03\xa8\x81\x02\xe8\x03\xf6\xe5\x01\xf0\x03\xaf\x13\xf8\x03\x84\x07\x80\x04\xe7\xf0\x01\x88\x04\xa8\x81\x02\x90\x04\xe7\xf0\x01\x98\x04\xa8\x81\x02\xc8\x04\x01\xd2\x04=/data/app/com.dts.freefireth-PdeDnOilCSFn37p1AH_FLg==/lib/arm\xe0\x04\x01\xea\x04_2087f61c19f57f2af4e7feff0b24d9d9|/data/app/com.dts.freefireth-PdeDnOilCSFn37p1AH_FLg==/base.apk\xf0\x04\x03\xf8\x04\x01\x8a\x05\x0232\x9a\x05\n2019118692\xb2\x05\tOpenGLES2\xb8\x05\xff\x7f\xc0\x05\x04\xe0\x05\xf3F\xea\x05\x07android\xf2\x05pKqsHT5ZLWrYljNb5Vqh//yFRlaPHSO9NWSQsVvOmdhEEn7W+VHNUK+Q+fduA3ptNrGB0Ll0LRz3WW0jOwesLj6aiU7sZ40p8BfUE/FI/jzSTwRe2\xf8\x05\xfb\xe4\x06\x88\x06\x01\x90\x06\x01\x9a\x06\x014\xa2\x06\x014\xb2\x06"GQ@O\x00\x0e^\x00D\x06UA\x0ePM\r\x13hZ\x07T\x06\x0cm\\V\x0ejYV;\x0bU5'
        ]
        payload = b''.join(payload_parts)
        if region in ["ME", "TH"]:
            url = "https://loginbp.common.ggbluefox.com/MajorLogin"
        else:
            url = "https://loginbp.ggblueshark.com/MajorLogin"
        headers = {
            "Accept-Encoding": "gzip", "Authorization": "Bearer", "Connection": "Keep-Alive",
            "Content-Type": "application/x-www-form-urlencoded", "Expect": "100-continue",
            "Host": "loginbp.ggblueshark.com" if region not in ["ME","TH"] else "loginbp.common.ggbluefox.com",
            "ReleaseVersion": "OB54", "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 9; ASUS_I005DA Build/PI)",
            "X-GA": "v1 1", "X-Unity-Version": "2018.4.11f1"
        }
        data = payload.replace(b'afcfbf13334be42036e4f742c80b956344bed760ac91b3aff9b607a610ab4390', access_token.encode())
        data = data.replace(b'1d8ec0240ede109973f3321b9354b44d', open_id.encode())
        d = encrypt_api(data.hex())
        session = requests.Session()
        session.verify = False
        response = session.post(url, headers=headers, data=bytes.fromhex(d), timeout=5)
        if response.status_code == 200 and len(response.text) > 10:
            jwt_start = response.text.find("eyJ")
            if jwt_start != -1:
                jwt_token = response.text[jwt_start:]
                second_dot = jwt_token.find(".", jwt_token.find(".") + 1)
                if second_dot != -1:
                    jwt_token = jwt_token[:second_dot + 44]
                try:
                    parts = jwt_token.split('.')
                    if len(parts) >= 2:
                        payload_part = parts[1]
                        padding = 4 - len(payload_part) % 4
                        if padding != 4:
                            payload_part += '=' * padding
                        decoded = base64.urlsafe_b64decode(payload_part)
                        data = json.loads(decoded)
                        account_id = data.get('account_id') or data.get('external_id')
                        if account_id:
                            return {"account_id": str(account_id), "jwt_token": jwt_token}
                except:
                    pass
        return {"account_id": "N/A", "jwt_token": ""}
    except:
        return {"account_id": "N/A", "jwt_token": ""}

def get_session():
    with session_lock:
        if session_pool:
            return session_pool.popleft()
    s = requests.Session()
    s.verify = False
    proxy = get_next_proxy()
    if proxy:
        s.proxies = {'http': proxy, 'https': proxy}
    return s

def return_session(s):
    with session_lock:
        if len(session_pool) < THREAD_COUNT * 2:
            session_pool.append(s)
        else:
            s.close()

for _ in range(min(10, THREAD_COUNT)):
    s = requests.Session()
    s.verify = False
    session_pool.append(s)

def read_file_safe(filepath):
    with file_lock:
        try:
            if os.path.exists(filepath):
                with open(filepath, 'r', encoding='utf-8') as f:
                    return f.read()
        except:
            pass
    return ""

def write_file_atomic(filepath, content):
    with file_lock:
        try:
            temp_fd, temp_path = tempfile.mkstemp(dir=os.path.dirname(filepath) or '.', text=True)
            try:
                with os.fdopen(temp_fd, 'w', encoding='utf-8') as f:
                    f.write(content)
                    f.flush()
                    os.fsync(f.fileno())
                shutil.move(temp_path, filepath)
            except:
                try:
                    os.unlink(temp_path)
                except:
                    pass
                raise
        except:
            pass

def append_file_atomic(filepath, content):
    with file_lock:
        try:
            existing = read_file_safe(filepath)
            new_content = existing + content
            write_file_atomic(filepath, new_content)
        except:
            pass

def load_output_mode():
    content = read_file_safe(OUTPUT_MODE_FILE).strip()
    return content if content else "clean"

def save_output_mode(mode):
    write_file_atomic(OUTPUT_MODE_FILE, mode)

def load_custom_name():
    content = read_file_safe(CUSTOM_NAME_FILE).strip()
    return content if content else ""

def save_custom_name(name):
    write_file_atomic(CUSTOM_NAME_FILE, name)

def load_rare_only():
    content = read_file_safe(RARE_ONLY_FILE).strip()
    return content == "true"

def save_rare_only(enabled):
    write_file_atomic(RARE_ONLY_FILE, "true" if enabled else "false")

def load_custom_letters():
    content = read_file_safe(CUSTOM_LETTERS_FILE).strip()
    if content and len(content) == 2 and content.isalpha():
        return content.upper()
    return "AB"

def save_custom_letters(letters):
    write_file_atomic(CUSTOM_LETTERS_FILE, letters.upper())

def get_device_fingerprint():
    with file_lock:
        try:
            content = read_file_safe(DEVICE_FILE).strip()
            if content:
                return content
            raw = secrets.token_hex(16)
            device_id = hashlib.sha256(raw.encode()).hexdigest()[:32]
            write_file_atomic(DEVICE_FILE, device_id)
            return device_id
        except:
            return hashlib.sha256(secrets.token_hex(16).encode()).hexdigest()[:32]

def get_user_key():
    with file_lock:
        try:
            content = read_file_safe(USER_KEY_FILE).strip()
            if content:
                return content
            device_id = get_device_fingerprint()
            raw_key = hashlib.sha256(device_id.encode()).hexdigest()[:15].upper()
            formatted = f"{raw_key[:5]}-{raw_key[5:10]}-{raw_key[10:15]}"
            write_file_atomic(USER_KEY_FILE, formatted)
            return formatted
        except:
            return "N/A"

def count_same_digits(account_id):
    aid = str(account_id)
    if not aid.isdigit() or len(aid) < 5:
        return 0, None
    analyzed = aid[1:]
    digit_counts = Counter(analyzed)
    max_count = max(digit_counts.values()) if digit_counts else 0
    most_digit = max(digit_counts, key=digit_counts.get) if digit_counts else None
    return max_count, most_digit

def generate_cool_name():
    letters = load_custom_letters()
    first_char = letters[0]
    second_char = letters[1]
    length = random.randint(8, 12)
    f_pos = random.randint(0, length - 1)
    k_pos = random.randint(0, length - 1)
    while k_pos == f_pos:
        k_pos = random.randint(0, length - 1)
    name = []
    for i in range(length):
        if i == f_pos:
            name.append(first_char)
        elif i == k_pos:
            name.append(second_char)
        else:
            name.append(random.choice(CHARS))
    return ''.join(name)

def generate_password():
    digits = ''.join(random.choices(string.digits, k=random.randint(4, 6)))
    letters = ''.join(random.choices(string.ascii_uppercase, k=random.randint(3, 5)))
    return f"XENONFLASHFF{digits}{letters}"

# ═══════════════════════════════════════════
# ACCOUNT GENERATION
# ═══════════════════════════════════════════

def generate_account():
    global last_success_time
    if not running:
        return None
    session = get_session()
    try:
        for retry in range(2):
            try:
                password = generate_password()
                name = generate_cool_name()
                resp = session.post(
                    "https://100067.connect.garena.com/api/v2/oauth/guest:register",
                    headers=get_headers(),
                    json={"app_id": 100067, "client_type": 2, "password": password, "source": 2},
                    timeout=5
                )
                if resp.status_code == 200:
                    data = resp.json()
                    if "data" in data and "uid" in data["data"]:
                        uid = data["data"]["uid"]
                        resp2 = session.post(
                            "https://100067.connect.garena.com/oauth/guest/token/grant",
                            headers=get_headers_form(),
                            data={"uid": uid, "password": password, "response_type": "token", "client_type": "2", "client_secret": HEX_KEY, "client_id": "100067"},
                            timeout=5
                        )
                        if resp2.status_code == 200:
                            token_data = resp2.json()
                            open_id = token_data.get('open_id', '')
                            access_token = token_data.get('access_token', '')
                            if open_id and access_token:
                                keystream = [0x30,0x30,0x30,0x32,0x30,0x31,0x37,0x30,0x30,0x30,0x30,0x30,0x32,0x30,0x31,0x37,0x30,0x30,0x30,0x30,0x30,0x32,0x30,0x31,0x37,0x30,0x30,0x30,0x30,0x30,0x32,0x30]
                                encoded = ""
                                for i in range(len(open_id)):
                                    encoded += chr(ord(open_id[i]) ^ keystream[i % len(keystream)])
                                hex_str = ''.join(c if 32 <= ord(c) <= 126 else '\\u{:04x}'.format(ord(c)) for c in encoded)
                                field = codecs.decode(hex_str, 'unicode_escape').encode('latin1')
                                if REGION in ["ME", "TH"]:
                                    url_major = "https://loginbp.common.ggbluefox.com/MajorRegister"
                                else:
                                    url_major = "https://loginbp.ggblueshark.com/MajorRegister"
                                lang_code = REGION_LANG.get(REGION, "en")
                                payload = {1: name, 2: access_token, 3: open_id, 5: 102000007, 6: 4, 7: 1, 13: 1, 14: field, 15: lang_code, 16: 1, 17: 1}
                                payload_bytes = build_proto(payload)
                                encrypted_payload = aes_encrypt(payload_bytes.hex())
                                headers_major = {
                                    "Accept-Encoding": "gzip", "Authorization": "Bearer", "Connection": "Keep-Alive",
                                    "Content-Type": "application/x-www-form-urlencoded", "Expect": "100-continue",
                                    "Host": "loginbp.ggblueshark.com" if REGION not in ["ME","TH"] else "loginbp.common.ggbluefox.com",
                                    "ReleaseVersion": "OB54", "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 9; ASUS_I005DA Build/PI)",
                                    "X-GA": "v1 1", "X-Unity-Version": "2018.4.11f1"
                                }
                                session.post(url_major, headers=headers_major, data=encrypted_payload, timeout=5)
                                login_result = major_login(uid, password, access_token, open_id, REGION)
                                account_id = login_result.get("account_id", "N/A")
                                jwt_token = login_result.get("jwt_token", "")
                                if account_id != "N/A":
                                    return_session(session)
                                    last_success_time = time.time()
                                    return {
                                        "uid": uid,
                                        "password": password,
                                        "name": name,
                                        "account_id": account_id,
                                        "jwt_token": jwt_token,
                                        "success": True
                                    }
            except:
                pass
    except:
        pass
    return_session(session)
    return None

# ═══════════════════════════════════════════
# BATCH & SAVE
# ═══════════════════════════════════════════

def add_to_batch(account_data):
    """Add rare account to batch queue and send if batch is full"""
    global batch_queue
    with batch_lock:
        batch_queue.append(account_data)
        if len(batch_queue) >= BATCH_SIZE:
            # Send batch
            batch_to_send = batch_queue.copy()
            batch_queue = []
            # Send in background thread
            threading.Thread(target=send_batch, args=(batch_to_send,), daemon=True).start()

def send_batch(batch_data):
    """Send batch of rare accounts to Telegram"""
    try:
        caption = f"📦 <b>BATCH RARE ACCOUNTS ({len(batch_data)} accounts)</b>\n"
        caption += f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        caption += f"🤖 ALVIN FF Bot"
        send_telegram_json(batch_data, caption)
    except Exception as e:
        print(f"[BATCH] Error sending batch: {e}")

def save_account_special(account_data, custom_name=""):
    try:
        same_count = account_data.get('same_digit_count', 0)
        most_digit = account_data.get('most_digit', '')
        uid = account_data.get('uid', 'N/A')
        aid = account_data.get('account_id', 'N/A')
        password = account_data.get('password', 'N/A')
        name = account_data.get('name', 'N/A')
        created_at = account_data.get('created_at', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        jwt_token = account_data.get('jwt_token', '')
        rarity_name = get_rarity_name(same_count)

        account_json_file = os.path.join(SPECIAL_FOLDER, "account.json")
        id_txt_file = os.path.join(SPECIAL_FOLDER, "id.txt")
        cariid_file = os.path.join(SPECIAL_FOLDER, "cariid.txt")
        rarity_file = os.path.join(SPECIAL_FOLDER, "by_rarity.txt")

        if same_count >= 5 and most_digit:
            cat_file = os.path.join(SPECIAL_FOLDER, f"{most_digit}.txt")
            cat_entry = f"{uid} | {aid} | {password} | [{rarity_name}]\n"
            append_file_atomic(cat_file, cat_entry)

        with file_lock:
            all_accounts = []
            if os.path.exists(account_json_file):
                try:
                    with open(account_json_file, 'r', encoding='utf-8') as f:
                        all_accounts = json.load(f)
                except:
                    all_accounts = []
            account_entry = {
                "uid": uid,
                "account_id": aid,
                "password": password,
                "name": name,
                "same_digit_count": same_count,
                "most_digit": most_digit,
                "rarity": rarity_name,
                "created_at": created_at,
                "jwt_token": jwt_token,
                "region": REGION_NAME,
                "custom_name": custom_name
            }
            all_accounts.append(account_entry)
            write_file_atomic(account_json_file, json.dumps(all_accounts, indent=2, ensure_ascii=False))

            all_ids = [acc.get('account_id', 'N/A') for acc in all_accounts]
            write_file_atomic(id_txt_file, '\n'.join(all_ids))

            all_entries = []
            header = ""
            if os.path.exists(cariid_file):
                content = read_file_safe(cariid_file)
                lines = content.split('\n')
                if lines:
                    header = lines[0] + '\n\n'
                    all_entries = [line for line in lines[2:] if line.strip()]
            if not header:
                header = "[9] [8] [7] [6] [5] (URUTAN SAME DIGIT TERBANYAK)\n\n"
            display_uid = f"{uid} | {password}" if custom_name else uid
            digit_info = f"{most_digit}x{same_count}" if most_digit else f"{same_count}x"
            new_entry = f"[{same_count}] {display_uid} | {aid} | {digit_info} | [{rarity_name}]"
            all_entries.append(new_entry)
            def sort_key(line):
                for digit in range(9, 0, -1):
                    if f"[{digit}]" in line:
                        return -digit
                return 0
            all_entries.sort(key=sort_key)
            final_content = header + '\n'.join(all_entries) + '\n'
            write_file_atomic(cariid_file, final_content)

            rarity_entry = f"[{rarity_name}] {uid} | {aid} | {password} | {digit_info}\n"
            append_file_atomic(rarity_file, rarity_entry)
    except Exception as e:
        pass

def save_account_all(account_data, custom_name=""):
    try:
        same_count = account_data.get('same_digit_count', 0)
        most_digit = account_data.get('most_digit', '')
        uid = account_data.get('uid', 'N/A')
        aid = account_data.get('account_id', 'N/A')
        password = account_data.get('password', 'N/A')
        name = account_data.get('name', 'N/A')
        created_at = account_data.get('created_at', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        jwt_token = account_data.get('jwt_token', '')
        rarity_name = get_rarity_name(same_count)

        account_json_file = os.path.join(ALL_FOLDER, "account.json")
        id_txt_file = os.path.join(ALL_FOLDER, "id.txt")

        with file_lock:
            all_accounts = []
            if os.path.exists(account_json_file):
                try:
                    with open(account_json_file, 'r', encoding='utf-8') as f:
                        all_accounts = json.load(f)
                except:
                    all_accounts = []
            account_entry = {
                "uid": uid,
                "account_id": aid,
                "password": password,
                "name": name,
                "same_digit_count": same_count,
                "most_digit": most_digit,
                "rarity": rarity_name,
                "created_at": created_at,
                "jwt_token": jwt_token,
                "region": REGION_NAME,
                "custom_name": custom_name
            }
            all_accounts.append(account_entry)
            write_file_atomic(account_json_file, json.dumps(all_accounts, indent=2, ensure_ascii=False))

            all_ids = [acc.get('account_id', 'N/A') for acc in all_accounts]
            write_file_atomic(id_txt_file, '\n'.join(all_ids))
    except:
        pass

# ═══════════════════════════════════════════
# WORKER
# ═══════════════════════════════════════════

def worker(output_mode, custom_name="", rare_only=False):
    global running, last_success_time, target_mode_active, target_id, target_progress
    while running:
        account = generate_account()
        if account and account.get("success"):
            uid = account["uid"]
            aid = account["account_id"]
            if aid == "N/A":
                aid = str(uid)
            password = account["password"]
            name = account["name"]
            jwt_token = account.get("jwt_token", "")
            same_count, most_digit = count_same_digits(aid)

            with stats_lock:
                stats['total'] += 1
                if same_count == 5:
                    stats['same_5'] += 1
                elif same_count == 6:
                    stats['same_6'] += 1
                elif same_count == 7:
                    stats['same_7'] += 1
                elif same_count == 8:
                    stats['same_8'] += 1
                elif same_count == 9:
                    stats['same_9'] += 1
                elif same_count == 10:
                    stats['same_10'] += 1
                elif same_count >= 11:
                    stats['same_11plus'] += 1
                current_no = stats['total']

            account_info = {
                'uid': uid,
                'password': password,
                'account_id': aid,
                'name': name,
                'region': REGION_NAME,
                'same_digit_count': same_count,
                'most_digit': most_digit,
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'watermark': WATERMARK,
                'jwt_token': jwt_token
            }

            if target_mode_active and target_id:
                if aid == target_id or uid == target_id:
                    send_telegram_message(
                        f"🎯 <b>TARGET FOUND!</b>\n\n"
                        f"<b>UID:</b> <code>{uid}</code>\n"
                        f"<b>Account ID:</b> <code>{aid}</code>\n"
                        f"<b>Password:</b> <code>{password}</code>\n"
                        f"<b>Time:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                    )
                    target_progress = 0
                else:
                    target_progress += 1
                    if target_progress % 100 == 0:
                        send_telegram_message(
                            f"🔍 <b>Target Search Progress</b>\n"
                            f"Checked: {target_progress} accounts\n"
                            f"Target: <code>{target_id}</code>"
                        )

            # Print to console
            rarity_name = get_rarity_name(same_count)
            if same_count >= 5:
                print(f"[{current_no}] {uid} | {aid} | {password} | {rarity_name} | {most_digit}x{same_count}")
            else:
                if output_mode == 'full':
                    print(f"[{current_no}] {uid} | {aid} | {password} | {rarity_name}")

            # Save & notify
            if same_count >= 5:
                save_account_special(account_info, custom_name)
                # Add to batch queue for Telegram
                add_to_batch(account_info)
                # Instant notification for 7+
                if same_count >= 7:
                    send_rare_notification(account_info)
            else:
                save_account_all(account_info, custom_name)

            last_success_time = time.time()
        else:
            time.sleep(FAIL_SLEEP)

# ═══════════════════════════════════════════
# TELEGRAM BOT POLLING
# ═══════════════════════════════════════════

bot_running = True
last_update_id = 0

def get_updates():
    global last_update_id
    try:
        url = f"{TELEGRAM_API}/getUpdates"
        params = {"offset": last_update_id + 1, "limit": 100}
        resp = requests.get(url, params=params, timeout=30)
        if resp.status_code == 200:
            data = resp.json()
            if data.get("ok"):
                return data.get("result", [])
    except Exception as e:
        print(f"[BOT] Error getting updates: {e}")
    return []

def send_message(chat_id, text, reply_to=None):
    try:
        url = f"{TELEGRAM_API}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "HTML",
            "disable_web_page_preview": True
        }
        if reply_to:
            payload["reply_to_message_id"] = reply_to
        resp = requests.post(url, json=payload, timeout=10)
        return resp.status_code == 200
    except Exception as e:
        print(f"[BOT] Error sending message: {e}")
        return False

def handle_command(message):
    global running, THREAD_COUNT, target_mode_active, target_id, stats

    chat_id = message["chat"]["id"]
    text = message.get("text", "")
    message_id = message["message_id"]

    if not text:
        return

    parts = text.split()
    command = parts[0].lower()

    if command == "/start":
        if running:
            send_message(chat_id, "⚠️ <b>Bot is already running!</b>\nUse /stop first, then /start again.", message_id)
            return

        # Parse args: /start <threads> <mode> <letters>
        # Default: 200 threads, mode 2 (full), letters AZ
        threads = 200
        mode = "2"  # default full mode
        letters = "AZ"

        if len(parts) >= 2:
            try:
                threads = int(parts[1])
                if threads < 1:
                    threads = 200
            except:
                threads = 200

        if len(parts) >= 3:
            mode = parts[2]

        if len(parts) >= 4:
            letters = parts[3].upper()
            if len(letters) != 2 or not letters.isalpha():
                letters = "AZ"

        # Set config
        THREAD_COUNT = threads
        save_custom_letters(letters)

        if mode == "2":
            output_mode = "full"
            save_output_mode("full")
        else:
            output_mode = "clean"
            save_output_mode("clean")

        # Reset stats
        stats['total'] = 0
        stats['same_5'] = 0
        stats['same_6'] = 0
        stats['same_7'] = 0
        stats['same_8'] = 0
        stats['same_9'] = 0
        stats['same_10'] = 0
        stats['same_11plus'] = 0
        stats['start_time'] = time.time()

        # Start generator
        running = True

        # Send start confirmation
        send_message(chat_id, 
            f"🚀 <b>ALVIN FF CHECKER STARTED!</b>\n\n"
            f"📊 <b>Config:</b>\n"
            f"• Threads: <code>{THREAD_COUNT}</code>\n"
            f"• Mode: <code>{'FULL' if output_mode == 'full' else 'CLEAN'}</code>\n"
            f"• Letters: <code>{letters}</code>\n"
            f"• Region: <code>{REGION_NAME}</code>\n\n"
            f"💎 Rare accounts (5x-9x) will be sent here\n"
            f"📦 Batch every {BATCH_SIZE} rare accounts\n"
            f"⚡ Instant notify for 7x+ accounts\n\n"
            f"Use /stop to stop | /log for stats",
            message_id
        )

        # Start workers in background
        def start_workers():
            try:
                with ThreadPoolExecutor(max_workers=THREAD_COUNT) as executor:
                    futures = [executor.submit(worker, output_mode, "", False) for _ in range(THREAD_COUNT)]
                    for future in as_completed(futures):
                        if not running:
                            executor.shutdown(wait=False, cancel_futures=True)
                            break
                        future.result()
            except Exception as e:
                print(f"[WORKER] Error: {e}")
                send_message(chat_id, f"❌ <b>Error:</b> <code>{str(e)}</code>")

        threading.Thread(target=start_workers, daemon=True).start()

    elif command == "/stop":
        if not running:
            send_message(chat_id, "⚠️ <b>Bot is not running!</b>", message_id)
            return

        running = False
        elapsed = time.time() - stats['start_time']

        # Send remaining batch
        global batch_queue
        with batch_lock:
            if batch_queue:
                remaining = batch_queue.copy()
                batch_queue = []
                threading.Thread(target=send_batch, args=(remaining,), daemon=True).start()

        send_message(chat_id,
            f"🛑 <b>ALVIN FF CHECKER STOPPED!</b>\n\n"
            f"📊 <b>Final Stats:</b>\n"
            f"• Total: <code>{stats['total']}</code>\n"
            f"• 5x: <code>{stats['same_5']}</code>\n"
            f"• 6x: <code>{stats['same_6']}</code>\n"
            f"• 7x: <code>{stats['same_7']}</code>\n"
            f"• 8x: <code>{stats['same_8']}</code>\n"
            f"• 9x+: <code>{stats['same_9'] + stats['same_10'] + stats['same_11plus']}</code>\n"
            f"⏱ Time: <code>{elapsed:.1f}s</code>\n"
            f"⚡ Speed: <code>{stats['total']/elapsed:.2f} acc/s</code>" if elapsed > 0 else "",
            message_id
        )

    elif command == "/log":
        elapsed = time.time() - stats['start_time']
        speed = stats['total']/elapsed if elapsed > 0 else 0

        send_message(chat_id,
            f"📊 <b>ALVIN FF LOG</b>\n\n"
            f"<b>Status:</b> {'🟢 RUNNING' if running else '🔴 STOPPED'}\n"
            f"<b>Total:</b> <code>{stats['total']}</code>\n"
            f"<b>5x:</b> <code>{stats['same_5']}</code>\n"
            f"<b>6x:</b> <code>{stats['same_6']}</code>\n"
            f"<b>7x:</b> <code>{stats['same_7']}</code>\n"
            f"<b>8x:</b> <code>{stats['same_8']}</code>\n"
            f"<b>9x+:</b> <code>{stats['same_9'] + stats['same_10'] + stats['same_11plus']}</code>\n"
            f"⏱ <b>Time:</b> <code>{elapsed:.1f}s</code>\n"
            f"⚡ <b>Speed:</b> <code>{speed:.2f} acc/s</code>\n"
            f"🔧 <b>Threads:</b> <code>{THREAD_COUNT}</code>",
            message_id
        )

    elif command == "/help":
        send_message(chat_id,
            f"🤖 <b>ALVIN FF TELEGRAM BOT</b>\n\n"
            f"<b>Commands:</b>\n"
            f"• /start &lt;threads&gt; &lt;mode&gt; &lt;letters&gt; - Start generator\n"
            f"  Example: <code>/start 200 2 AZ</code>\n"
            f"  Mode: 1=clean, 2=full\n"
            f"• /stop - Stop generator\n"
            f"• /log - Show statistics\n"
            f"• /help - Show this help\n\n"
            f"<b>Features:</b>\n"
            f"💎 Auto-detect rare accounts (5x-9x)\n"
            f"📦 Batch send every 10 rare accounts\n"
            f"⚡ Instant notify for 7x+ accounts\n"
            f"📁 Save to ALVIN_FF/special/ & allaccount/",
            message_id
        )
    else:
        send_message(chat_id, "❓ Unknown command. Use /help for available commands.", message_id)

def bot_polling_loop():
    """Main bot polling loop"""
    global last_update_id, bot_running

    print("[BOT] Telegram bot polling started...")
    send_telegram_message("🤖 <b>ALVIN FF Bot is ONLINE!</b>\n\nUse /start to begin generation\nUse /help for commands")

    while bot_running:
        try:
            updates = get_updates()
            for update in updates:
                last_update_id = update["update_id"]
                if "message" in update:
                    message = update["message"]
                    if "text" in message:
                        handle_command(message)
            time.sleep(1)
        except Exception as e:
            print(f"[BOT] Polling error: {e}")
            time.sleep(5)

# ═══════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════

def main():
    global PROXY_LIST

    # Load proxies
    PROXY_LIST = load_proxies_from_file()

    print(f"""
╔══════════════════════════════════════════╗
║   ALVIN FF CHECKER - TELEGRAM BOT v2.0   ║
║                                          ║
║   🤖 Telegram Bot Mode                   ║
║   📦 Auto batch send (every 10 rare)     ║
║   ⚡ Instant notify 7x+                  ║
║                                          ║
╚══════════════════════════════════════════╝
    """)

    print(f"[CONFIG] Bot Token: {BOT_TOKEN[:20]}...")
    print(f"[CONFIG] Chat ID: {CHAT_ID}")
    print(f"[CONFIG] Batch Size: {BATCH_SIZE}")
    print()

    # Start bot polling in main thread
    bot_polling_loop()

if __name__ == "__main__":
    try:
        from Crypto.Cipher import AES
        from Crypto.Util.Padding import pad
        main()
    except ImportError:
        print("[ERROR] pip install pycryptodome")
        sys.exit(0)
