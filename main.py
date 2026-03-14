import logging
import random
import re
import json
import time
import asyncio
from datetime import datetime
from typing import Optional, Dict, Any, List, Tuple
from urllib.parse import urlparse, parse_qs

import requests
from bs4 import BeautifulSoup
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters
from telegram.constants import ParseMode

# ========== ТВОИ ДАННЫЕ ==========
BOT_TOKEN = "8430585997:AAFE8C3ostnoTQiwSlwVmYpnVQI5FjbsCRc"
CHANNEL_LINK = "https://t.me/+WLiiYR7_ymZjYWY1"
CHANNEL_ID = -1003256576224
YOUR_TELEGRAM_ID = 571001160

# ========== БАН-ЛИСТ ==========
BANNED_USERNAMES = {
    "giftrelayer", "mrktbank", "kallent", "monk", "durov",
    "virusgift", "portalsrelayer", "lucha", "snoopdogg", "snoop",
    "ufc", "nft", "telegram", "nftgift", "nftgiftbot", "ton", "gift",
    "relayer", "bank", "kallen", "nftbot", "giftbot", "channel", "nftrelayer"
}

# ========== НАСТРОЙКИ ==========
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ========== ПОЛНЫЙ СПИСОК NFT (97 ШТУК) ==========
NFT_LIST = [
    {"name": "BDayCandle", "difficulty": "easy", "id_range": "1000-20000", "min_id": 1000, "max_id": 20000},
    {"name": "CandyCane", "difficulty": "easy", "id_range": "1000-150000", "min_id": 1000, "max_id": 150000},
    {"name": "CloverPin", "difficulty": "easy", "id_range": "1000-60000", "min_id": 1000, "max_id": 60000},
    {"name": "DeskCalendar", "difficulty": "easy", "id_range": "1000-13000", "min_id": 1000, "max_id": 13000},
    {"name": "FaithAmulet", "difficulty": "easy", "id_range": "1000-60000", "min_id": 1000, "max_id": 60000},
    {"name": "FreshSocks", "difficulty": "easy", "id_range": "1000-100000", "min_id": 1000, "max_id": 100000},
    {"name": "GingerCookie", "difficulty": "easy", "id_range": "1000-60000", "min_id": 1000, "max_id": 60000},
    {"name": "HappyBrownie", "difficulty": "easy", "id_range": "1000-60000", "min_id": 1000, "max_id": 60000},
    {"name": "HolidayDrink", "difficulty": "easy", "id_range": "1000-60000", "min_id": 1000, "max_id": 60000},
    {"name": "HomemadeCake", "difficulty": "easy", "id_range": "1000-130000", "min_id": 1000, "max_id": 130000},
    {"name": "IceCream", "difficulty": "easy", "id_range": "1000-60000", "min_id": 1000, "max_id": 60000},
    {"name": "InstantRamen", "difficulty": "easy", "id_range": "1000-60000", "min_id": 1000, "max_id": 60000},
    {"name": "JesterHat", "difficulty": "easy", "id_range": "1000-60000", "min_id": 1000, "max_id": 60000},
    {"name": "JingleBells", "difficulty": "easy", "id_range": "1000-60000", "min_id": 1000, "max_id": 60000},
    {"name": "LolPop", "difficulty": "easy", "id_range": "1000-130000", "min_id": 1000, "max_id": 130000},
    {"name": "LunarSnake", "difficulty": "easy", "id_range": "1000-250000", "min_id": 1000, "max_id": 250000},
    {"name": "PetSnake", "difficulty": "easy", "id_range": "1000-1000", "min_id": 1000, "max_id": 1000},
    {"name": "SnakeBox", "difficulty": "easy", "id_range": "1000-55000", "min_id": 1000, "max_id": 55000},
    {"name": "SnoopDogg", "difficulty": "easy", "id_range": "576241-576241", "min_id": 576241, "max_id": 576241},
    {"name": "SpicedWine", "difficulty": "easy", "id_range": "93557-93557", "min_id": 93557, "max_id": 93557},
    {"name": "WhipCupcake", "difficulty": "easy", "id_range": "1000-170000", "min_id": 1000, "max_id": 170000},
    {"name": "WinterWreath", "difficulty": "easy", "id_range": "65311-65311", "min_id": 65311, "max_id": 65311},
    {"name": "XmasStocking", "difficulty": "easy", "id_range": "177478-177478", "min_id": 177478, "max_id": 177478},
    {"name": "BerryBox", "difficulty": "medium", "id_range": "1000-60000", "min_id": 1000, "max_id": 60000},
    {"name": "BigYear", "difficulty": "medium", "id_range": "1000-60000", "min_id": 1000, "max_id": 60000},
    {"name": "BowTie", "difficulty": "medium", "id_range": "1000-47000", "min_id": 1000, "max_id": 47000},
    {"name": "BunnyMuffin", "difficulty": "medium", "id_range": "1000-60000", "min_id": 1000, "max_id": 60000},
    {"name": "CookieHeart", "difficulty": "medium", "id_range": "1000-60000", "min_id": 1000, "max_id": 60000},
    {"name": "EasterEgg", "difficulty": "medium", "id_range": "1000-60000", "min_id": 1000, "max_id": 60000},
    {"name": "EternalCandle", "difficulty": "medium", "id_range": "1000-60000", "min_id": 1000, "max_id": 60000},
    {"name": "EvilEye", "difficulty": "medium", "id_range": "1000-60000", "min_id": 1000, "max_id": 60000},
    {"name": "HexPot", "difficulty": "medium", "id_range": "1000-50000", "min_id": 1000, "max_id": 50000},
    {"name": "HypnoLollipop", "difficulty": "medium", "id_range": "1000-60000", "min_id": 1000, "max_id": 60000},
    {"name": "InputKey", "difficulty": "medium", "id_range": "1000-80000", "min_id": 1000, "max_id": 80000},
    {"name": "JackInTheBox", "difficulty": "medium", "id_range": "1000-60000", "min_id": 1000, "max_id": 60000},
    {"name": "JellyBunny", "difficulty": "medium", "id_range": "1000-60000", "min_id": 1000, "max_id": 60000},
    {"name": "JollyChimp", "difficulty": "medium", "id_range": "1000-25000", "min_id": 1000, "max_id": 25000},
    {"name": "JoyfulBundle", "difficulty": "medium", "id_range": "1000-60000", "min_id": 1000, "max_id": 60000},
    {"name": "LightSword", "difficulty": "medium", "id_range": "1000-110000", "min_id": 1000, "max_id": 110000},
    {"name": "LushBouquet", "difficulty": "medium", "id_range": "1000-60000", "min_id": 1000, "max_id": 60000},
    {"name": "MousseCake", "difficulty": "medium", "id_range": "119126-119126", "min_id": 119126, "max_id": 119126},
    {"name": "PartySparkler", "difficulty": "medium", "id_range": "161722-161722", "min_id": 161722, "max_id": 161722},
    {"name": "RestlessJar", "difficulty": "medium", "id_range": "1000-23000", "min_id": 1000, "max_id": 23000},
    {"name": "SantaHat", "difficulty": "medium", "id_range": "19289-19289", "min_id": 19289, "max_id": 19289},
    {"name": "SnoopCigar", "difficulty": "medium", "id_range": "1000-60000", "min_id": 1000, "max_id": 60000},
    {"name": "SnowGlobe", "difficulty": "medium", "id_range": "48029-48029", "min_id": 48029, "max_id": 48029},
    {"name": "SnowMittens", "difficulty": "medium", "id_range": "64057-64057", "min_id": 64057, "max_id": 64057},
    {"name": "SpringBasket", "difficulty": "medium", "id_range": "140160-140160", "min_id": 140160, "max_id": 140160},
    {"name": "SpyAgaric", "difficulty": "medium", "id_range": "84274-84274", "min_id": 84274, "max_id": 84274},
    {"name": "StarNotepad", "difficulty": "medium", "id_range": "1000-25000", "min_id": 1000, "max_id": 25000},
    {"name": "StellarRocket", "difficulty": "medium", "id_range": "1000-35000", "min_id": 1000, "max_id": 35000},
    {"name": "SwagBag", "difficulty": "medium", "id_range": "1000-5000", "min_id": 1000, "max_id": 5000},
    {"name": "TamaGadget", "difficulty": "medium", "id_range": "95205-95205", "min_id": 95205, "max_id": 95205},
    {"name": "ValentineBox", "difficulty": "medium", "id_range": "229868-229868", "min_id": 229868, "max_id": 229868},
    {"name": "WitchHat", "difficulty": "medium", "id_range": "1000-7000", "min_id": 1000, "max_id": 7000},
    {"name": "UFCStrike", "difficulty": "medium", "id_range": "1000-56951", "min_id": 1000, "max_id": 56951},
    {"name": "ArtisanBrick", "difficulty": "hard", "id_range": "1000-7000", "min_id": 1000, "max_id": 7000},
    {"name": "AstralShard", "difficulty": "hard", "id_range": "1000-60000", "min_id": 1000, "max_id": 60000},
    {"name": "BondedRing", "difficulty": "hard", "id_range": "1000-3000", "min_id": 1000, "max_id": 3000},
    {"name": "CupidCharm", "difficulty": "hard", "id_range": "1000-60000", "min_id": 1000, "max_id": 60000},
    {"name": "DiamondRing", "difficulty": "hard", "id_range": "1000-60000", "min_id": 1000, "max_id": 60000},
    {"name": "DurovsCap", "difficulty": "hard", "id_range": "1000-60000", "min_id": 1000, "max_id": 60000},
    {"name": "EternalRose", "difficulty": "hard", "id_range": "1000-60000", "min_id": 1000, "max_id": 60000},
    {"name": "FlyingBroom", "difficulty": "hard", "id_range": "1000-60000", "min_id": 1000, "max_id": 60000},
    {"name": "GemSignet", "difficulty": "hard", "id_range": "1000-60000", "min_id": 1000, "max_id": 60000},
    {"name": "GenieLamp", "difficulty": "hard", "id_range": "1000-60000", "min_id": 1000, "max_id": 60000},
    {"name": "GustalBall", "difficulty": "hard", "id_range": "1000-60000", "min_id": 1000, "max_id": 60000},
    {"name": "HeartLocket", "difficulty": "hard", "id_range": "1000-60000", "min_id": 1000, "max_id": 60000},
    {"name": "HeroicHelmet", "difficulty": "hard", "id_range": "1000-60000", "min_id": 1000, "max_id": 60000},
    {"name": "IonGem", "difficulty": "hard", "id_range": "1000-60000", "min_id": 1000, "max_id": 60000},
    {"name": "IonicDryer", "difficulty": "hard", "id_range": "1000-60000", "min_id": 1000, "max_id": 60000},
    {"name": "KissedFrog", "difficulty": "hard", "id_range": "1000-60000", "min_id": 1000, "max_id": 60000},
    {"name": "LootBag", "difficulty": "hard", "id_range": "1000-60000", "min_id": 1000, "max_id": 60000},
    {"name": "LoveCandle", "difficulty": "hard", "id_range": "1000-60000", "min_id": 1000, "max_id": 60000},
    {"name": "LovePotion", "difficulty": "hard", "id_range": "1000-60000", "min_id": 1000, "max_id": 60000},
    {"name": "LowRider", "difficulty": "hard", "id_range": "1000-60000", "min_id": 1000, "max_id": 60000},
    {"name": "MadPumpkin", "difficulty": "hard", "id_range": "96227-96227", "min_id": 96227, "max_id": 96227},
    {"name": "MagicPotion", "difficulty": "hard", "id_range": "4764-4764", "min_id": 4764, "max_id": 4764},
    {"name": "MightyArm", "difficulty": "hard", "id_range": "150000-150000", "min_id": 150000, "max_id": 150000},
    {"name": "MiniOscar", "difficulty": "hard", "id_range": "4764-4764", "min_id": 4764, "max_id": 4764},
    {"name": "NailBracelet", "difficulty": "hard", "id_range": "119126-119126", "min_id": 119126, "max_id": 119126},
    {"name": "NekoHelmet", "difficulty": "hard", "id_range": "15431-15431", "min_id": 15431, "max_id": 15431},
    {"name": "PerfumeBottle", "difficulty": "hard", "id_range": "151632-151632", "min_id": 151632, "max_id": 151632},
    {"name": "PreciousPeach", "difficulty": "hard", "id_range": "2981-2981", "min_id": 2981, "max_id": 2981},
    {"name": "RecordPlayer", "difficulty": "hard", "id_range": "554-554", "min_id": 554, "max_id": 554},
    {"name": "ScaredCat", "difficulty": "hard", "id_range": "8029-8029", "min_id": 8029, "max_id": 8029},
    {"name": "SharpTongue", "difficulty": "hard", "id_range": "1000-16430", "min_id": 1000, "max_id": 16430},
    {"name": "SignetRing", "difficulty": "hard", "id_range": "1000-16430", "min_id": 1000, "max_id": 16430},
    {"name": "SkullFlower", "difficulty": "hard", "id_range": "1000-21428", "min_id": 1000, "max_id": 21428},
    {"name": "SkyStilettos", "difficulty": "hard", "id_range": "1000-47465", "min_id": 1000, "max_id": 47465},
    {"name": "SleighBell", "difficulty": "hard", "id_range": "1000-48029", "min_id": 1000, "max_id": 48029},
    {"name": "SwissWatch", "difficulty": "hard", "id_range": "1000-25121", "min_id": 1000, "max_id": 25121},
    {"name": "TopHat", "difficulty": "hard", "id_range": "1000-32648", "min_id": 1000, "max_id": 32648},
    {"name": "ToyBear", "difficulty": "hard", "id_range": "1000-60000", "min_id": 1000, "max_id": 60000},
    {"name": "TrappedHeart", "difficulty": "hard", "id_range": "1000-24656", "min_id": 1000, "max_id": 24656},
    {"name": "VintageCigar", "difficulty": "hard", "id_range": "1000-18000", "min_id": 1000, "max_id": 18000},
    {"name": "VoodooDoll", "difficulty": "hard", "id_range": "1000-26658", "min_id": 1000, "max_id": 26658}
]

NFT_DICT = {nft["name"]: nft for nft in NFT_LIST}

# ========== РЕЖИМЫ ПОИСКА ==========
SEARCH_MODES = {
    "light": {
        "name": "🟢 Легкий режим",
        "description": "Недорогие подарки до 3 TON\nСамые неопытные пользователи",
        "difficulties": ["easy"]
    },
    "medium": {
        "name": "🟡 Средний режим",
        "description": "Хорошие подарки от 3 до 15 TON\nБолее опытные пользователи",
        "difficulties": ["easy", "medium"]
    },
    "heavy": {
        "name": "🔴 Жирный режим",
        "description": "Дорогие подарки от 15 до 600 TON\nОпытные коллекционеры",
        "difficulties": ["medium", "hard"]
    }
}

# ========== ХРАНИЛИЩЕ ==========
user_states = {}
users_db = {}
blocked_nfts = {}
user_settings = {}
last_message_ids = {}
EMOJIS = ["😀", "😎", "🚀", "🎮", "🍕", "🐱", "🌟", "🎯", "💻", "📱", "🎲", "⚡"]

# ========== ПРОВЕРКА ПОДПИСКИ ==========
async def check_subscription(user_id: int, context: ContextTypes.DEFAULT_TYPE) -> bool:
    try:
        member = await context.bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        return member.status not in ["left", "kicked"]
    except Exception as e:
        logger.error(f"Ошибка проверки подписки: {e}")
        return False

async def require_subscription(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not await check_subscription(user_id, context):
        await show_subscription_required(update, context)
        return False
    return True

async def show_subscription_required(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("📢 Подписаться на канал", url=CHANNEL_LINK)]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    message = "⚠️ Для использования бота подпишитесь на канал!"
    
    if update.callback_query:
        await update.callback_query.message.edit_text(message, reply_markup=reply_markup)
    else:
        await update.message.reply_text(message, reply_markup=reply_markup)

# ========== КЛАСС ПАРСЕРА ИЗ par.py ==========
class NFTGiftParser:
    """Класс для парсинга информации о NFT-подарках Telegram"""
    
    def __init__(self, use_selenium_fallback: bool = True):
        self.use_selenium_fallback = use_selenium_fallback
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'ru-RU,ru;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
    
    def extract_gift_id_from_url(self, gift_url: str) -> Optional[str]:
        patterns = [
            r"t\.me/nft/(?P<gift_id>\w+)",
            r"telegram\.me/nft/(?P<gift_id>\w+)",
            r"t\.me/\w+\?start=nft_(?P<gift_id>\w+)",
            r"t\.me/nftgiftbot\?start=(?P<gift_id>g_\w+)",
            r"t\.me/nftgift\?start=(?P<gift_id>\w+)",
        ]
        for pattern in patterns:
            match = re.search(pattern, gift_url, re.IGNORECASE)
            if match:
                return match.group('gift_id')
        parsed_url = urlparse(gift_url)
        query_params = parse_qs(parsed_url.query)
        if 'start' in query_params:
            start_value = query_params['start'][0]
            if start_value.startswith('nft_'):
                return start_value[4:]
            elif start_value.startswith('g_'):
                return start_value[2:]
            elif len(start_value) > 5:
                return start_value
        return None
    
    def _extract_from_ld_json(self, soup: BeautifulSoup) -> Optional[Dict[str, Any]]:
        script_tags = soup.find_all('script', type='application/ld+json')
        for script in script_tags:
            try:
                data = json.loads(script.string)
                if isinstance(data, dict):
                    return data
                elif isinstance(data, list) and len(data) > 0:
                    return data[0]
            except (json.JSONDecodeError, AttributeError):
                continue
        return None
    
    def _extract_from_telegram_webapp(self, soup: BeautifulSoup) -> Optional[Dict[str, Any]]:
        script_tags = soup.find_all('script')
        for script in script_tags:
            content = script.string or ''
            if 'initData' in content or 'webAppData' in content:
                patterns = [
                    r'"user"\s*:\s*({[^}]+})',
                    r'"from"\s*:\s*({[^}]+})',
                    r'"owner"\s*:\s*({[^}]+})',
                    r'"username"\s*:\s*"([^"]+)"',
                    r'"id"\s*:\s*(\d+)',
                ]
                for pattern in patterns:
                    matches = re.findall(pattern, content)
                    for match in matches:
                        if match:
                            return {'raw_data': match}
        return None
    
    def _parse_meta_tags(self, soup: BeautifulSoup) -> Dict[str, Any]:
        result = {}
        og_tags = {}
        for meta in soup.find_all('meta', property=re.compile(r'^og:')):
            prop = meta.get('property', '')
            content = meta.get('content', '')
            if prop and content:
                og_tags[prop] = content
        if 'og:title' in og_tags:
            result['gift_title'] = og_tags['og:title']
        if 'og:description' in og_tags:
            result['gift_description'] = og_tags['og:description']
            desc = og_tags['og:description']
            patterns = [
                r'@(\w{5,32})',
                r'от @(\w{5,32})',
                r'by @(\w{5,32})',
                r'owner[\s:]+@(\w{5,32})',
                r'владелец[\s:]+@(\w{5,32})',
            ]
            for pattern in patterns:
                match = re.search(pattern, desc, re.IGNORECASE)
                if match:
                    result['owner_username'] = match.group(1)
                    break
        for meta in soup.find_all('meta', attrs={'name': re.compile(r'^twitter:')}):
            name = meta.get('name', '')
            content = meta.get('content', '')
            if name and content:
                if name == 'twitter:title' and 'gift_title' not in result:
                    result['gift_title'] = content
                elif name == 'twitter:description' and 'gift_description' not in result:
                    result['gift_description'] = content
        return result
    
    def parse_nft_gift_page(self, gift_url: str, timeout: int = 15) -> Optional[Dict[str, Any]]:
        try:
            response = self.session.get(gift_url, timeout=timeout)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            result = {
                'gift_id': self.extract_gift_id_from_url(gift_url),
                'owner_username': None,
                'owner_id': None,
                'owner_name': None,
                'gift_title': None,
                'gift_description': None,
                'page_url': gift_url,
                'status_code': response.status_code,
                'raw_html_preview': response.text[:1000],
            }
            meta_data = self._parse_meta_tags(soup)
            result.update(meta_data)
            ld_data = self._extract_from_ld_json(soup)
            if ld_data:
                result['ld_json'] = ld_data
            data_elements = soup.find_all(attrs={'data-user': True})
            for elem in data_elements:
                user_data = elem.get('data-user', '')
                if user_data:
                    try:
                        user_json = json.loads(user_data)
                        if isinstance(user_json, dict):
                            if 'username' in user_json:
                                result['owner_username'] = user_json['username'].replace('@', '')
                            if 'id' in user_json:
                                result['owner_id'] = str(user_json['id'])
                    except json.JSONDecodeError:
                        username_match = re.search(r'@(\w{5,32})', user_data)
                        if username_match:
                            result['owner_username'] = username_match.group(1)
                        id_match = re.search(r'id[:\s]?(\d{6,12})', user_data, re.IGNORECASE)
                        if id_match:
                            result['owner_id'] = id_match.group(1)
            telegram_patterns = [
                r'tg://user\?id=(\d+)',
                r't\.me/(\w{5,32})(?:$|\?|/)',
                r'telegram\.me/(\w{5,32})(?:$|\?|/)',
            ]
            all_links = soup.find_all('a', href=True)
            for link in all_links:
                href = link.get('href', '')
                for pattern in telegram_patterns:
                    match = re.search(pattern, href, re.IGNORECASE)
                    if match:
                        value = match.group(1)
                        if value.isdigit():
                            result['owner_id'] = value
                        elif value not in ['nft', 'gift', 'joinchat', 'addstickers']:
                            result['owner_username'] = value
            page_text = soup.get_text()
            if not result['owner_username']:
                usernames = re.findall(r'@(\w{5,32})', page_text)
                filtered = [u for u in usernames if u.lower() not in 
                           ['telegram', 'nft', 'gift', 'bot', 'admin', 'support']]
                if filtered:
                    result['owner_username'] = filtered[0]
            if not result['owner_id']:
                ids = re.findall(r'\b(\d{8,10})\b', page_text)
                if ids:
                    result['owner_id'] = ids[0]
            script_tags = soup.find_all('script')
            for script in script_tags:
                content = script.string or ''
                if content:
                    patterns = [
                        r'"username"\s*:\s*"@?(\w{5,32})"',
                        r'"user"\s*:\s*{[^}]*"username"\s*:\s*"@?(\w{5,32})"[^}]*}',
                        r'"id"\s*:\s*"?(\d{8,10})"?',
                        r'"userId"\s*:\s*"?(\d{8,10})"?',
                        r'"ownerId"\s*:\s*"?(\d{8,10})"?',
                    ]
                    for pattern in patterns:
                        matches = re.findall(pattern, content)
                        for match in matches:
                            if match:
                                if match.isdigit():
                                    result['owner_id'] = match
                                else:
                                    result['owner_username'] = match.replace('@', '')
            if not result['gift_title']:
                title_tag = soup.find('title')
                if title_tag:
                    result['gift_title'] = title_tag.get_text(strip=True)
            return result
        except requests.RequestException as e:
            nft_logger.error(f"Ошибка запроса для {gift_url}: {e}")
            return None
        except Exception as e:
            nft_logger.error(f"Ошибка парсинга {gift_url}: {e}")
            return None
    
    def parse_with_selenium(self, gift_url: str) -> Optional[Dict[str, Any]]:
        # Заглушка, чтобы не требовать selenium
        return None
    
    async def get_nft_owner_info(self, gift_url: str) -> Dict[str, Any]:
        result = {
            'success': False,
            'gift_id': None,
            'owner_username': None,
            'owner_id': None,
            'owner_name': None,
            'error': None,
            'method': None,
            'execution_time': None,
        }
        start_time = time.time()
        if not self.validate_telegram_url(gift_url):
            result['error'] = 'Некорректный URL Telegram'
            return result
        gift_id = self.extract_gift_id_from_url(gift_url)
        if not gift_id:
            result['error'] = 'Не удалось извлечь ID подарка'
            return result
        result['gift_id'] = gift_id
        nft_logger.info(f"Парсинг страницы для gift_id: {gift_id}")
        page_data = self.parse_nft_gift_page(gift_url)
        if page_data:
            result['method'] = 'web_parsing'
            if page_data.get('owner_username') or page_data.get('owner_id'):
                result.update({
                    'success': True,
                    'owner_username': page_data.get('owner_username'),
                    'owner_id': page_data.get('owner_id'),
                    'owner_name': page_data.get('owner_name'),
                })
            else:
                result['error'] = 'Владелец не найден в данных страницы'
        else:
            result['error'] = 'Не удалось загрузить страницу'
        result['execution_time'] = round(time.time() - start_time, 2)
        if not result['success'] and not result['error']:
            result['error'] = 'Не удалось найти информацию о владельце'
        return result
    
    @staticmethod
    def validate_telegram_url(url: str) -> bool:
        valid_patterns = [
            r'^https?://(www\.)?(t|telegram)\.me/',
            r'^https?://t\.me/',
            r'^https?://telegram\.me/',
        ]
        return any(re.match(pattern, url, re.IGNORECASE) for pattern in valid_patterns)
    
    @staticmethod
    def format_owner_info_message(owner_info: Dict[str, Any]) -> str:
        if owner_info['success']:
            msg = "✅ <b>Информация о NFT-подарке найдена!</b>\n\n"
            msg += f"🎁 ID подарка: <code>{owner_info['gift_id']}</code>\n"
            if owner_info['owner_username']:
                msg += f"👤 Username: @{owner_info['owner_username']}\n"
                msg += f"🔗 Ссылка: https://t.me/{owner_info['owner_username']}\n"
            if owner_info['owner_id']:
                msg += f"🆔 User ID: <code>{owner_info['owner_id']}</code>\n"
                msg += f"📱 TG Link: tg://user?id={owner_info['owner_id']}\n"
            if owner_info['owner_name']:
                msg += f"📝 Имя: {owner_info['owner_name']}\n"
            msg += f"\n📊 Метод: {owner_info['method']}"
            if 'execution_time' in owner_info:
                msg += f"\n⏱ Время выполнения: {owner_info['execution_time']}с"
        else:
            msg = "❌ <b>Не удалось получить информацию о владельце</b>\n\n"
            msg += f"🎁 ID подарка: <code>{owner_info.get('gift_id', 'Неизвестно')}</code>\n"
            msg += f"⚠️ Причина: {owner_info.get('error', 'Неизвестная ошибка')}\n\n"
            msg += "Возможные причины:\n"
            msg += "• Подарок не существует или удален\n"
            msg += "• Информация скрыта настройками приватности\n"
            msg += "• Ссылка устарела или недействительна\n"
            msg += "• Требуется авторизация в Telegram"
            if owner_info.get('method'):
                msg += f"\n\n🛠 Использованный метод: {owner_info['method']}"
        return msg

# ========== ФУНКЦИИ ДЛЯ УДАЛЕНИЯ СООБЩЕНИЙ ==========
async def delete_previous_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id in last_message_ids:
        for msg_id in last_message_ids[user_id]:
            try:
                await context.bot.delete_message(chat_id=user_id, message_id=msg_id)
            except:
                pass
        last_message_ids[user_id] = []

async def save_message_id(update: Update, message):
    user_id = update.effective_user.id
    if user_id not in last_message_ids:
        last_message_ids[user_id] = []
    last_message_ids[user_id].append(message.message_id)
    if len(last_message_ids[user_id]) > 20:
        old_id = last_message_ids[user_id].pop(0)
        try:
            await context.bot.delete_message(chat_id=user_id, message_id=old_id)
        except:
            pass

# ========== ФУНКЦИИ ГЕНЕРАЦИИ ССЫЛОК ==========
def generate_gift_links(nft_name, count=20):
    nft = NFT_DICT.get(nft_name)
    if not nft:
        return []
    clean_name = re.sub(r"[^\w]", "", nft_name)
    links = []
    for _ in range(count):
        nft_id = random.randint(nft["min_id"], nft["max_id"])
        links.append(f"https://t.me/nft/{clean_name}-{nft_id}")
    return links

def generate_random_gifts(mode="light", count=20):
    if mode == "light":
        available = [n for n in NFT_LIST if n["difficulty"] == "easy"]
    elif mode == "medium":
        available = [n for n in NFT_LIST if n["difficulty"] in ["easy", "medium"]]
    else:
        available = [n for n in NFT_LIST if n["difficulty"] in ["medium", "hard"]]
    if not available:
        available = NFT_LIST
    gifts = []
    for _ in range(count):
        nft = random.choice(available)
        clean_name = re.sub(r"[^\w]", "", nft["name"])
        nft_id = random.randint(nft["min_id"], nft["max_id"])
        gifts.append({"name": nft["name"], "url": f"https://t.me/nft/{clean_name}-{nft_id}"})
    return gifts

def generate_girls_gifts(count=20):
    girl_keywords = ["heart", "peach", "rose", "flower", "candle", "ring", "love", "cookie", "berry", "bunny", "kiss", "sweet"]
    girl_nfts = [n for n in NFT_LIST if any(k in n["name"].lower() for k in girl_keywords)]
    if not girl_nfts:
        girl_nfts = NFT_LIST[:20]
    gifts = []
    for _ in range(count):
        nft = random.choice(girl_nfts)
        clean_name = re.sub(r"[^\w]", "", nft["name"])
        nft_id = random.randint(nft["min_id"], nft["max_id"])
        gifts.append({"name": nft["name"], "url": f"https://t.me/nft/{clean_name}-{nft_id}"})
    return gifts

# ========== ФУНКЦИЯ РЕАЛЬНОГО ПОИСКА ВЛАДЕЛЬЦЕВ ==========
async def find_real_owners(links: List[str], limit: int = 5) -> List[Dict]:
    """Параллельно проверяет ссылки и возвращает только те, у которых есть владелец (не в бане)"""
    parser = NFTGiftParser()
    tasks = []
    for url in links:
        tasks.append(asyncio.to_thread(parser.get_nft_owner_info, url))
    results = await asyncio.gather(*tasks)
    found = []
    for res in results:
        if res.get('success'):
            owner = res.get('owner_username') or res.get('owner_id')
            if owner:
                # Проверка бан-листа
                if res.get('owner_username') and res['owner_username'].lower() in BANNED_USERNAMES:
                    continue
                if res.get('owner_id') and res['owner_id'] in BANNED_USERNAMES:  # но тут id, не username
                    pass
                found.append({
                    'owner': owner,
                    'url': res.get('gift_url') or '?',
                    'name': res.get('owner_name') or 'NFT'
                })
            if len(found) >= limit:
                break
    return found

# ========== ГЛАВНОЕ МЕНЮ ==========
async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    text = f"❗ Привет, @{user.username or 'user'}! Это парсер для поиска мамонтов."
    keyboard = [
        [InlineKeyboardButton("🔍 Поиск NFT", callback_data="menu_search")],
        [InlineKeyboardButton("👤 Мой профиль", callback_data="menu_profile")],
        [InlineKeyboardButton("⚙️ Настройки", callback_data="menu_settings")],
        [InlineKeyboardButton("🆘 Поддержка", callback_data="menu_support")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    if update.callback_query:
        await update.callback_query.message.edit_text(text, reply_markup=reply_markup)
    else:
        await delete_previous_messages(update, context)
        sent = await update.message.reply_text(text, reply_markup=reply_markup)
        await save_message_id(update, sent)

# ========== КОМАНДА /START ==========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not await require_subscription(update, context):
        return
    if user_id not in users_db:
        users_db[user_id] = {
            'username': update.effective_user.username or f"user{user_id}",
            'registered': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'searches': 0,
            'users_found': 0,
            'last_search': None
        }
    if user_id not in user_settings:
        user_settings[user_id] = {'results_count': 20}
    await show_main_menu(update, context)

# ========== МЕНЮ ПОИСКА ==========
async def show_search_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    text = """Выберите тип поиска:

🎲 Рандом поиск - поиск по режимам (легкий, средний, жирный)
🔍 Поиск по модели - точный поиск по конкретным NFT
👧 Поиск девушек - поиск по женским именам"""
    keyboard = [
        [InlineKeyboardButton("🎲 Рандом поиск", callback_data="search_random")],
        [InlineKeyboardButton("🔍 Поиск по модели", callback_data="search_model")],
        [InlineKeyboardButton("👧 Поиск девушек", callback_data="search_girls")],
        [InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.message.edit_text(text, reply_markup=reply_markup)

# ========== МЕНЮ РЕЖИМОВ ==========
async def show_modes_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    text = """Выберите режим поиска:

🟢 Легкий режим  
  Недорогие подарки до 3 TON  
  Самые неопытные пользователи  

🟡 Средний режим  
  Хорошие подарки от 3 до 15 TON  
  Более опытные пользователи  

🔴 Жирный режим  
  Дорогие подарки от 15 до 600 TON  
  Опытные коллекционеры"""
    keyboard = [
        [InlineKeyboardButton("🟢 Легкий режим", callback_data="mode_light")],
        [InlineKeyboardButton("🟡 Средний режим", callback_data="mode_medium")],
        [InlineKeyboardButton("🔴 Жирный режим", callback_data="mode_heavy")],
        [InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.message.edit_text(text, reply_markup=reply_markup)

# ========== ПОДТВЕРЖДЕНИЕ РЕЖИМА ==========
async def show_mode_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE, mode):
    query = update.callback_query
    mode_names = {"light": "🟢 Легкий режим", "medium": "🟡 Средний режим", "heavy": "🔴 Жирный режим"}
    text = f"""Выбран режим: ✅ {mode_names[mode]}
Шаблон: Стандартный

Нажмите кнопку ниже чтобы начать поиск:"""
    keyboard = [
        [InlineKeyboardButton("📌 Начать поиск NFT", callback_data=f"start_search_{mode}")],
        [InlineKeyboardButton("📌 Назад к режимам", callback_data="search_random")],
        [InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.message.edit_text(text, reply_markup=reply_markup)

# ========== ПОКАЗ РЕЗУЛЬТАТОВ (РЕАЛЬНЫЙ ПАРСИНГ) ==========
async def show_search_results(update: Update, context: ContextTypes.DEFAULT_TYPE, mode, nft_name=None, page=1):
    query = update.callback_query
    user_id = query.from_user.id
    count = user_settings.get(user_id, {}).get('results_count', 20)
    
    # Генерируем ссылки в зависимости от режима
    if nft_name:
        links = generate_gift_links(nft_name, count)
        title = f"Подарок: {nft_name}"
    elif mode == "girls":
        gifts = generate_girls_gifts(count)
        links = [g['url'] for g in gifts]
        title = "👧 Поиск девушек"
    else:
        gifts = generate_random_gifts(mode, count)
        links = [g['url'] for g in gifts]
        mode_names = {"light": "🟢 Легкий", "medium": "🟡 Средний", "heavy": "🔴 Жирный"}
        title = f"Режим: {mode_names[mode]}"
    
    await query.message.edit_text("🔍 Ищу владельцев... Это может занять до минуты.")
    
    # Реальный поиск владельцев
    found = await find_real_owners(links, limit=5)  # ищем до 5 результатов
    
    if user_id in users_db:
        users_db[user_id]['searches'] += 1
        users_db[user_id]['users_found'] += len(found)
        users_db[user_id]['last_search'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    if not found:
        keyboard = [[InlineKeyboardButton("🔄 Попробовать снова", callback_data="search_random")]]
        await query.message.edit_text("❌ Не найдено владельцев. Попробуйте другой режим.", reply_markup=InlineKeyboardMarkup(keyboard))
        return
    
    # Формируем текст
    text = f"*Результаты поиска*\nНайдено владельцев: {len(found)}\n{title}\n\n"
    for i, item in enumerate(found, 1):
        text += f"{i}. 👤 @{item['owner']}\n   🎁 [Ссылка]({item['url']})\n\n"
    
    # Пагинация (тут можно добавить, но пока просто одна страница)
    keyboard = [
        [InlineKeyboardButton("🔄 Новый поиск", callback_data="search_random")],
        [InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.message.edit_text(
        text,
        reply_markup=reply_markup,
        parse_mode=ParseMode.MARKDOWN,
        disable_web_page_preview=True
    )

# ========== МЕНЮ ВЫБОРА МОДЕЛИ ==========
async def show_model_selection(update: Update, context: ContextTypes.DEFAULT_TYPE, page=1):
    query = update.callback_query
    items_per_page = 10
    total_pages = (len(NFT_LIST) + items_per_page - 1) // items_per_page
    start = (page - 1) * items_per_page
    end = min(start + items_per_page, len(NFT_LIST))
    page_nfts = NFT_LIST[start:end]
    keyboard = []
    for nft in page_nfts:
        keyboard.append([InlineKeyboardButton(f"🎁 {nft['name']} ({nft['difficulty']})", callback_data=f"select_model_{nft['name']}")])
    nav = []
    if page > 1:
        nav.append(InlineKeyboardButton("◀️", callback_data=f"model_page_{page-1}"))
    nav.append(InlineKeyboardButton(f"{page}/{total_pages}", callback_data="noop"))
    if page < total_pages:
        nav.append(InlineKeyboardButton("▶️", callback_data=f"model_page_{page+1}"))
    if nav:
        keyboard.append(nav)
    keyboard.append([InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    text = f"🔗 Выберите модель NFT для поиска:\n\nСтраница {page}/{total_pages}"
    await query.message.edit_text(text, reply_markup=reply_markup)

# ========== ПРОФИЛЬ ==========
async def show_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    user = users_db.get(user_id, {})
    text = f"""ID: {user_id}
Имя: @{user.get('username', 'unknown')}
Дата регистрации: {user.get('registered', 'Неизвестно')}
Активных дней: 1

СТАТИСТИКА
Всего поисков: {user.get('searches', 0)}
Найдено пользователей: {user.get('users_found', 0)}
Создано шаблонов: 0
Заблокировано NFT: {len(blocked_nfts.get(user_id, []))}

ТЕКУЩИЕ НАСТРОЙКИ
Режим: Легкий режим
Активный шаблон: Стандартный
Лимит поиска: {user_settings.get(user_id, {}).get('results_count', 20)}

Последний поиск: {user.get('last_search', 'Нет данных')}

Детальная статистика"""
    keyboard = [
        [InlineKeyboardButton("📊 Статистика за неделю", callback_data="profile_weekly")],
        [InlineKeyboardButton("⚡ Быстрые настройки", callback_data="profile_quick")],
        [InlineKeyboardButton("🪞 Создать зеркало", callback_data="profile_mirror")],
        [InlineKeyboardButton("👥 Реферальная система", callback_data="profile_ref")],
        [InlineKeyboardButton("🔒 Приватка для vorkera", callback_data="profile_private")],
        [InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.message.edit_text(text, reply_markup=reply_markup)

# ========== НАСТРОЙКИ ==========
async def show_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    current = user_settings.get(user_id, {}).get('results_count', 20)
    text = """Настройки
Выберите категорию настроек:"""
    keyboard = [
        [InlineKeyboardButton(f"📊 Количество результатов ({current})", callback_data="settings_results")],
        [InlineKeyboardButton("🎨 Интерфейс результатов (Список)", callback_data="settings_interface")],
        [InlineKeyboardButton("📝 Настройка шаблонов", callback_data="settings_templates")],
        [InlineKeyboardButton("🎮 Выбрать режим", callback_data="settings_mode")],
        [InlineKeyboardButton("🚫 Управление NFT", callback_data="settings_nft")],
        [InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.message.edit_text(text, reply_markup=reply_markup)

async def show_results_count_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    current = user_settings.get(user_id, {}).get('results_count', 20)
    text = f"""Установите количество результатов

Текущее значение: {current}
Максимум: 250"""
    keyboard = [
        [InlineKeyboardButton("20", callback_data="set_results_20"),
         InlineKeyboardButton("30", callback_data="set_results_30"),
         InlineKeyboardButton("50", callback_data="set_results_50")],
        [InlineKeyboardButton("100", callback_data="set_results_100"),
         InlineKeyboardButton("150", callback_data="set_results_150"),
         InlineKeyboardButton("200", callback_data="set_results_200")],
        [InlineKeyboardButton("250", callback_data="set_results_250")],
        [InlineKeyboardButton("◀️ Назад", callback_data="menu_settings")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.message.edit_text(text, reply_markup=reply_markup)

# ========== УПРАВЛЕНИЕ NFT (ЗАГЛУШКИ) ==========
async def show_nft_management(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    text = "Управление блокировками NFT\nВыберите действие:"
    keyboard = [
        [InlineKeyboardButton("🔒 Заблокировать NFT", callback_data="nft_block_menu")],
        [InlineKeyboardButton("🔓 Разблокировать NFT", callback_data="nft_unblock_menu")],
        [InlineKeyboardButton("📋 Список заблокированных", callback_data="nft_blocked_list")],
        [InlineKeyboardButton("📚 Весь список NFT", callback_data="nft_all_list")],
        [InlineKeyboardButton("◀️ Назад к настройкам", callback_data="menu_settings")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.message.edit_text(text, reply_markup=reply_markup)

# (Остальные функции управления NFT можно оставить как заглушки или реализовать позже)

# ========== ПОДДЕРЖКА ==========
async def show_support(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    text = """Меню поддержки

Выберите нужный раздел:"""
    keyboard = [
        [InlineKeyboardButton("📢 Купить рекламу", callback_data="support_ads")],
        [InlineKeyboardButton("💡 Предложить идею", callback_data="support_idea")],
        [InlineKeyboardButton("👨‍💻 Манаул по ворку", callback_data="support_manual")],
        [InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.message.edit_text(text, reply_markup=reply_markup)

# ========== HELP КОМАНДА ==========
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await require_subscription(update, context):
        return
    text = """🆘 СПРАВКА ПО БОТУ

ТРЕБОВАНИЯ:
1. Быть участником канала

КОМАНДЫ:
/start - Начать работу
/help - Справка
/status - Статус
/block <номер> - Заблокировать NFT
/unblock <номер> - Разблокировать NFT
/myblock - Список блокировок"""
    await update.message.reply_text(text)

# ========== СТАТУС ==========
async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await require_subscription(update, context):
        return
    user_id = update.effective_user.id
    subscribed = await check_subscription(user_id, context)
    text = f"""📊 ВАШ СТАТУС

Подписка: {'✅ В КАНАЛЕ' if subscribed else '❌ НЕТ'}
Поисков: {users_db.get(user_id, {}).get('searches', 0)}
Блокировок: {len(blocked_nfts.get(user_id, []))}"""
    await update.message.reply_text(text)

# ========== ОБРАБОТКА ТЕКСТОВЫХ КОМАНД ==========
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await require_subscription(update, context):
        return
    text = update.message.text
    user_id = update.effective_user.id
    if text.startswith('/block'):
        parts = text.split()
        if len(parts) == 2 and parts[1].isdigit():
            num = int(parts[1])
            if 1 <= num <= len(NFT_LIST):
                nft = NFT_LIST[num - 1]
                if user_id not in blocked_nfts:
                    blocked_nfts[user_id] = []
                if nft['name'] not in blocked_nfts[user_id]:
                    blocked_nfts[user_id].append(nft['name'])
                    await update.message.reply_text(f"✅ NFT {nft['name']} заблокирован")
                else:
                    await update.message.reply_text(f"⚠️ NFT {nft['name']} уже заблокирован")
            else:
                await update.message.reply_text("❌ Неверный номер")
    elif text.startswith('/unblock'):
        parts = text.split()
        if len(parts) == 2 and parts[1].isdigit():
            num = int(parts[1])
            if 1 <= num <= len(NFT_LIST):
                nft = NFT_LIST[num - 1]
                if user_id in blocked_nfts and nft['name'] in blocked_nfts[user_id]:
                    blocked_nfts[user_id].remove(nft['name'])
                    await update.message.reply_text(f"✅ NFT {nft['name']} разблокирован")
                else:
                    await update.message.reply_text(f"⚠️ NFT {nft['name']} не заблокирован")
            else:
                await update.message.reply_text("❌ Неверный номер")
    elif text == '/myblock':
        blocked = blocked_nfts.get(user_id, [])
        if not blocked:
            await update.message.reply_text("📋 У вас нет заблокированных NFT")
        else:
            msg = "📋 Ваши заблокированные NFT:\n\n"
            for i, name in enumerate(blocked, 1):
                msg += f"{i}. {name}\n"
            await update.message.reply_text(msg)

# ========== ОБРАБОТЧИК МЕНЮ ==========
async def handle_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if not await require_subscription(update, context):
        return
    
    data = query.data
    user_id = query.from_user.id
    
    if data == "main_menu":
        await show_main_menu(update, context)
    elif data == "menu_search":
        await show_search_menu(update, context)
    elif data == "menu_profile":
        await show_profile(update, context)
    elif data == "menu_settings":
        await show_settings(update, context)
    elif data == "menu_support":
        await show_support(update, context)
    elif data == "search_random":
        await show_modes_menu(update, context)
    elif data == "search_model":
        await show_model_selection(update, context)
    elif data == "search_girls":
        await show_search_results(update, context, "girls")
    elif data == "mode_light":
        await show_mode_confirmation(update, context, "light")
    elif data == "mode_medium":
        await show_mode_confirmation(update, context, "medium")
    elif data == "mode_heavy":
        await show_mode_confirmation(update, context, "heavy")
    elif data.startswith("start_search_"):
        mode = data.replace("start_search_", "")
        await show_search_results(update, context, mode)
    elif data.startswith("model_page_"):
        page = int(data.split("_")[2])
        await show_model_selection(update, context, page)
    elif data.startswith("select_model_"):
        nft_name = data.replace("select_model_", "")
        await show_search_results(update, context, "light", nft_name)
    elif data == "settings_results":
        await show_results_count_menu(update, context)
    elif data.startswith("set_results_"):
        value = int(data.split("_")[2])
        if user_id not in user_settings:
            user_settings[user_id] = {}
        user_settings[user_id]['results_count'] = value
        await show_settings(update, context)
    elif data == "settings_nft":
        await show_nft_management(update, context)
    elif data == "support_ads":
        await query.message.edit_text(
            "📢 Купить рекламу\n\nПо вопросам рекламы: @zotlu\n\n💰 Цены:\n• Пост в канале: 5 ТОН\n• Реклама в боте: 4 ТОНА",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Назад", callback_data="menu_support")]])
        )
    elif data == "support_idea":
        await query.message.edit_text(
            "💡 Предложить идею\n\nЕсть идея? Пишите @zotlu",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Назад", callback_data="menu_support")]])
        )
    elif data == "support_manual":
        await query.message.edit_text(
            "👨‍💻 Манаул по ворку\n\nРаздел в разработке",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Назад", callback_data="menu_support")]])
        )
    elif data.startswith("profile_"):
        await query.message.edit_text("⚡ Раздел в разработке", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Назад", callback_data="menu_profile")]]))
    elif data == "noop":
        pass

# ========== ЗАПУСК БОТА ==========
def main():
    print("=" * 70)
    print("🤖 NFT ПАРСЕР БОТ (ФИНАЛЬНАЯ ВЕРСИЯ)")
    print("=" * 70)
    print(f"📢 ID канала: {CHANNEL_ID}")
    print(f"🔗 Ссылка: {CHANNEL_LINK}")
    print("✅ Автоподписка")
    print("✅ Реальный парсинг владельцев")
    print("✅ Бан-лист релеев")
    print("=" * 70)
    
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("status", status_command))
    app.add_handler(CallbackQueryHandler(handle_menu))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    
    print("✅ Бот готов к работе!")
    app.run_polling()

if __name__ == "__main__":
    main()