import logging
import re
import json
import time
import asyncio
import random
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

# ========== БАН-ЛИСТ (РЕЛЕИ И СОЗДАТЕЛИ) ==========
BANNED_USERNAMES = {
    "giftrelayer", "mrktbank", "kallent", "monk", "durov",
    "virusgift", "portalsrelayer", "lucha", "snoopdogg", "snoop", 
    "ufc", "nft", "telegram", "nftgift", "nftgiftbot", "ton", "gift",
    "relayer", "bank", "kallen", "nftbot", "giftbot", "channel", "nftrelayer",
    "nftcollector", "nftmarket", "nfttrade", "nftshop", "nftstore"
}

# ========== НАСТРОЙКИ ==========
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ========== ХРАНИЛИЩЕ ==========
users_db = {}
user_settings = {}
last_message_ids = {}

# ========== ПОЛНЫЙ СПИСОК NFT (97 ШТУК) ==========
NFT_LIST = [
    # EASY
    {"name": "BDayCandle", "difficulty": "easy", "min_id": 1000, "max_id": 20000},
    {"name": "CandyCane", "difficulty": "easy", "min_id": 1000, "max_id": 150000},
    {"name": "CloverPin", "difficulty": "easy", "min_id": 1000, "max_id": 60000},
    {"name": "DeskCalendar", "difficulty": "easy", "min_id": 1000, "max_id": 13000},
    {"name": "FaithAmulet", "difficulty": "easy", "min_id": 1000, "max_id": 60000},
    {"name": "FreshSocks", "difficulty": "easy", "min_id": 1000, "max_id": 100000},
    {"name": "GingerCookie", "difficulty": "easy", "min_id": 1000, "max_id": 60000},
    {"name": "HappyBrownie", "difficulty": "easy", "min_id": 1000, "max_id": 60000},
    {"name": "HolidayDrink", "difficulty": "easy", "min_id": 1000, "max_id": 60000},
    {"name": "HomemadeCake", "difficulty": "easy", "min_id": 1000, "max_id": 130000},
    {"name": "IceCream", "difficulty": "easy", "min_id": 1000, "max_id": 60000},
    {"name": "InstantRamen", "difficulty": "easy", "min_id": 1000, "max_id": 60000},
    {"name": "JesterHat", "difficulty": "easy", "min_id": 1000, "max_id": 60000},
    {"name": "JingleBells", "difficulty": "easy", "min_id": 1000, "max_id": 60000},
    {"name": "LolPop", "difficulty": "easy", "min_id": 1000, "max_id": 130000},
    {"name": "LunarSnake", "difficulty": "easy", "min_id": 1000, "max_id": 250000},
    {"name": "PetSnake", "difficulty": "easy", "min_id": 1000, "max_id": 1000},
    {"name": "SnakeBox", "difficulty": "easy", "min_id": 1000, "max_id": 55000},
    {"name": "SnoopDogg", "difficulty": "easy", "min_id": 576241, "max_id": 576241},
    {"name": "SpicedWine", "difficulty": "easy", "min_id": 93557, "max_id": 93557},
    {"name": "WhipCupcake", "difficulty": "easy", "min_id": 1000, "max_id": 170000},
    {"name": "WinterWreath", "difficulty": "easy", "min_id": 65311, "max_id": 65311},
    {"name": "XmasStocking", "difficulty": "easy", "min_id": 177478, "max_id": 177478},
    
    # MEDIUM
    {"name": "BerryBox", "difficulty": "medium", "min_id": 1000, "max_id": 60000},
    {"name": "BigYear", "difficulty": "medium", "min_id": 1000, "max_id": 60000},
    {"name": "BowTie", "difficulty": "medium", "min_id": 1000, "max_id": 47000},
    {"name": "BunnyMuffin", "difficulty": "medium", "min_id": 1000, "max_id": 60000},
    {"name": "CookieHeart", "difficulty": "medium", "min_id": 1000, "max_id": 60000},
    {"name": "EasterEgg", "difficulty": "medium", "min_id": 1000, "max_id": 60000},
    {"name": "EternalCandle", "difficulty": "medium", "min_id": 1000, "max_id": 60000},
    {"name": "EvilEye", "difficulty": "medium", "min_id": 1000, "max_id": 60000},
    {"name": "HexPot", "difficulty": "medium", "min_id": 1000, "max_id": 50000},
    {"name": "HypnoLollipop", "difficulty": "medium", "min_id": 1000, "max_id": 60000},
    {"name": "InputKey", "difficulty": "medium", "min_id": 1000, "max_id": 80000},
    {"name": "JackInTheBox", "difficulty": "medium", "min_id": 1000, "max_id": 60000},
    {"name": "JellyBunny", "difficulty": "medium", "min_id": 1000, "max_id": 60000},
    {"name": "JollyChimp", "difficulty": "medium", "min_id": 1000, "max_id": 25000},
    {"name": "JoyfulBundle", "difficulty": "medium", "min_id": 1000, "max_id": 60000},
    {"name": "LightSword", "difficulty": "medium", "min_id": 1000, "max_id": 110000},
    {"name": "LushBouquet", "difficulty": "medium", "min_id": 1000, "max_id": 60000},
    {"name": "MousseCake", "difficulty": "medium", "min_id": 119126, "max_id": 119126},
    {"name": "PartySparkler", "difficulty": "medium", "min_id": 161722, "max_id": 161722},
    {"name": "RestlessJar", "difficulty": "medium", "min_id": 1000, "max_id": 23000},
    {"name": "SantaHat", "difficulty": "medium", "min_id": 19289, "max_id": 19289},
    {"name": "SnoopCigar", "difficulty": "medium", "min_id": 1000, "max_id": 60000},
    {"name": "SnowGlobe", "difficulty": "medium", "min_id": 48029, "max_id": 48029},
    {"name": "SnowMittens", "difficulty": "medium", "min_id": 64057, "max_id": 64057},
    {"name": "SpringBasket", "difficulty": "medium", "min_id": 140160, "max_id": 140160},
    {"name": "SpyAgaric", "difficulty": "medium", "min_id": 84274, "max_id": 84274},
    {"name": "StarNotepad", "difficulty": "medium", "min_id": 1000, "max_id": 25000},
    {"name": "StellarRocket", "difficulty": "medium", "min_id": 1000, "max_id": 35000},
    {"name": "SwagBag", "difficulty": "medium", "min_id": 1000, "max_id": 5000},
    {"name": "TamaGadget", "difficulty": "medium", "min_id": 95205, "max_id": 95205},
    {"name": "ValentineBox", "difficulty": "medium", "min_id": 229868, "max_id": 229868},
    {"name": "WitchHat", "difficulty": "medium", "min_id": 1000, "max_id": 7000},
    {"name": "UFCStrike", "difficulty": "medium", "min_id": 1000, "max_id": 56951},
    
    # HARD
    {"name": "ArtisanBrick", "difficulty": "hard", "min_id": 1000, "max_id": 7000},
    {"name": "AstralShard", "difficulty": "hard", "min_id": 1000, "max_id": 60000},
    {"name": "BondedRing", "difficulty": "hard", "min_id": 1000, "max_id": 3000},
    {"name": "CupidCharm", "difficulty": "hard", "min_id": 1000, "max_id": 60000},
    {"name": "DiamondRing", "difficulty": "hard", "min_id": 1000, "max_id": 60000},
    {"name": "DurovsCap", "difficulty": "hard", "min_id": 1000, "max_id": 60000},
    {"name": "EternalRose", "difficulty": "hard", "min_id": 1000, "max_id": 60000},
    {"name": "FlyingBroom", "difficulty": "hard", "min_id": 1000, "max_id": 60000},
    {"name": "GemSignet", "difficulty": "hard", "min_id": 1000, "max_id": 60000},
    {"name": "GenieLamp", "difficulty": "hard", "min_id": 1000, "max_id": 60000},
    {"name": "GustalBall", "difficulty": "hard", "min_id": 1000, "max_id": 60000},
    {"name": "HeartLocket", "difficulty": "hard", "min_id": 1000, "max_id": 60000},
    {"name": "HeroicHelmet", "difficulty": "hard", "min_id": 1000, "max_id": 60000},
    {"name": "IonGem", "difficulty": "hard", "min_id": 1000, "max_id": 60000},
    {"name": "IonicDryer", "difficulty": "hard", "min_id": 1000, "max_id": 60000},
    {"name": "KissedFrog", "difficulty": "hard", "min_id": 1000, "max_id": 60000},
    {"name": "LootBag", "difficulty": "hard", "min_id": 1000, "max_id": 60000},
    {"name": "LoveCandle", "difficulty": "hard", "min_id": 1000, "max_id": 60000},
    {"name": "LovePotion", "difficulty": "hard", "min_id": 1000, "max_id": 60000},
    {"name": "LowRider", "difficulty": "hard", "min_id": 1000, "max_id": 60000},
    {"name": "MadPumpkin", "difficulty": "hard", "min_id": 96227, "max_id": 96227},
    {"name": "MagicPotion", "difficulty": "hard", "min_id": 4764, "max_id": 4764},
    {"name": "MightyArm", "difficulty": "hard", "min_id": 150000, "max_id": 150000},
    {"name": "MiniOscar", "difficulty": "hard", "min_id": 4764, "max_id": 4764},
    {"name": "NailBracelet", "difficulty": "hard", "min_id": 119126, "max_id": 119126},
    {"name": "NekoHelmet", "difficulty": "hard", "min_id": 15431, "max_id": 15431},
    {"name": "PerfumeBottle", "difficulty": "hard", "min_id": 151632, "max_id": 151632},
    {"name": "PreciousPeach", "difficulty": "hard", "min_id": 2981, "max_id": 2981},
    {"name": "RecordPlayer", "difficulty": "hard", "min_id": 554, "max_id": 554},
    {"name": "ScaredCat", "difficulty": "hard", "min_id": 8029, "max_id": 8029},
    {"name": "SharpTongue", "difficulty": "hard", "min_id": 1000, "max_id": 16430},
    {"name": "SignetRing", "difficulty": "hard", "min_id": 1000, "max_id": 16430},
    {"name": "SkullFlower", "difficulty": "hard", "min_id": 1000, "max_id": 21428},
    {"name": "SkyStilettos", "difficulty": "hard", "min_id": 1000, "max_id": 47465},
    {"name": "SleighBell", "difficulty": "hard", "min_id": 1000, "max_id": 48029},
    {"name": "SwissWatch", "difficulty": "hard", "min_id": 1000, "max_id": 25121},
    {"name": "TopHat", "difficulty": "hard", "min_id": 1000, "max_id": 32648},
    {"name": "ToyBear", "difficulty": "hard", "min_id": 1000, "max_id": 60000},
    {"name": "TrappedHeart", "difficulty": "hard", "min_id": 1000, "max_id": 24656},
    {"name": "VintageCigar", "difficulty": "hard", "min_id": 1000, "max_id": 18000},
    {"name": "VoodooDoll", "difficulty": "hard", "min_id": 1000, "max_id": 26658}
]

NFT_DICT = {nft["name"]: nft for nft in NFT_LIST}

# ========== КЛАСС ПАРСЕРА (ТВОЙ) ==========
class NFTGiftParser:
    def __init__(self, use_selenium_fallback: bool = True):
        self.use_selenium_fallback = use_selenium_fallback
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml',
            'Accept-Language': 'ru-RU,ru;q=0.9,en;q=0.8',
            'Connection': 'keep-alive',
        })
    
    def extract_gift_id_from_url(self, gift_url: str) -> Optional[str]:
        patterns = [
            r"t\.me/nft/(?P<gift_id>\w+)",
            r"telegram\.me/nft/(?P<gift_id>\w+)",
        ]
        for pattern in patterns:
            match = re.search(pattern, gift_url, re.IGNORECASE)
            if match:
                return match.group('gift_id')
        return None
    
    def parse_nft_gift_page(self, gift_url: str, timeout: int = 10) -> Optional[Dict[str, Any]]:
        try:
            response = self.session.get(gift_url, timeout=timeout)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            result = {
                'gift_id': self.extract_gift_id_from_url(gift_url),
                'owner_username': None,
                'owner_id': None,
                'gift_title': None,
                'success': False
            }
            
            # Поиск в data-атрибутах
            data_elements = soup.find_all(attrs={'data-user': True})
            for elem in data_elements:
                user_data = elem.get('data-user', '')
                if user_data:
                    try:
                        user_json = json.loads(user_data)
                        if isinstance(user_json, dict):
                            if 'username' in user_json:
                                result['owner_username'] = user_json['username'].replace('@', '')
                                result['success'] = True
                            if 'id' in user_json:
                                result['owner_id'] = str(user_json['id'])
                    except:
                        username_match = re.search(r'@(\w{5,32})', user_data)
                        if username_match:
                            result['owner_username'] = username_match.group(1)
                            result['success'] = True
            
            # Поиск в тексте
            if not result['success']:
                page_text = soup.get_text()
                usernames = re.findall(r'@(\w{5,32})', page_text)
                filtered = [u for u in usernames if u.lower() not in 
                           ['telegram', 'nft', 'gift', 'bot', 'admin', 'support']]
                if filtered:
                    result['owner_username'] = filtered[0]
                    result['success'] = True
            
            # Поиск в скриптах
            if not result['success']:
                script_tags = soup.find_all('script')
                for script in script_tags:
                    content = script.string or ''
                    username_match = re.search(r'"username"\s*:\s*"@?(\w{5,32})"', content)
                    if username_match:
                        result['owner_username'] = username_match.group(1)
                        result['success'] = True
                        break
            
            return result
            
        except Exception as e:
            logger.error(f"Ошибка парсинга {gift_url}: {e}")
            return None
    
    async def get_nft_owner_info(self, gift_url: str) -> Dict[str, Any]:
        result = {
            'success': False,
            'gift_id': self.extract_gift_id_from_url(gift_url),
            'owner_username': None,
            'owner_id': None,
            'error': None,
        }
        
        page_data = self.parse_nft_gift_page(gift_url)
        
        if page_data and page_data.get('success'):
            username = page_data.get('owner_username', '').lower()
            if username and username not in BANNED_USERNAMES:
                result['success'] = True
                result['owner_username'] = username
                result['owner_id'] = page_data.get('owner_id')
        else:
            result['error'] = 'Владелец не найден'
        
        return result

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
    keyboard = [[InlineKeyboardButton("📢 Подписаться", url=CHANNEL_LINK)]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    message = "╔══════════════════════════╗\n║     ⚠️ ПОДПИСКА         ║\n╚══════════════════════════╝\n\nДля использования бота подпишитесь на канал!"
    
    if update.callback_query:
        await update.callback_query.message.edit_text(message, reply_markup=reply_markup)
    else:
        await update.message.reply_text(message, reply_markup=reply_markup)

# ========== ГЛАВНОЕ МЕНЮ ==========
async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    
    text = "╔══════════════════════════╗\n"
    text += "║     🚀 NFT ПАРСЕР       ║\n"
    text += "╚══════════════════════════╝\n\n"
    text += f"👋 Привет, @{user.username or 'user'}!\n\n"
    text += "🔍 Поиск владельцев NFT\n"
    text += f"📊 В базе: {len(NFT_LIST)} NFT\n"
    text += "🚫 Бан-лист релеев"
    
    keyboard = [
        [InlineKeyboardButton("🔍 НАЙТИ ВЛАДЕЛЬЦЕВ", callback_data="search")],
        [InlineKeyboardButton("📢 ПОДПИСАТЬСЯ", url=CHANNEL_LINK)]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.callback_query:
        await update.callback_query.message.edit_text(text, reply_markup=reply_markup)
    else:
        await delete_previous_messages(update, context)
        sent = await update.message.reply_text(text, reply_markup=reply_markup)
        await save_message_id(update, sent)

# ========== КОМАНДА START ==========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    username = update.effective_user.username or f"user{user_id}"
    
    if not await require_subscription(update, context):
        return
    
    if user_id not in users_db:
        users_db[user_id] = {
            'username': username,
            'registered': datetime.now().strftime("%Y-%m-%d"),
            'searches': 0,
            'found': 0
        }
    
    await show_main_menu(update, context)

# ========== ФУНКЦИЯ ПОИСКА ВЛАДЕЛЬЦЕВ ==========
async def find_owners(count=5):
    parser = NFTGiftParser()
    results = []
    used_ids = set()
    attempts = 0
    max_attempts = 100
    
    while len(results) < count and attempts < max_attempts:
        nft = random.choice(NFT_LIST)
        nft_id = random.randint(nft["min_id"], nft["max_id"])
        
        if nft_id in used_ids:
            attempts += 1
            continue
        
        clean_name = re.sub(r"[^\w]", "", nft["name"])
        url = f"https://t.me/nft/{clean_name}-{nft_id}"
        
        owner_info = await parser.get_nft_owner_info(url)
        
        if owner_info['success'] and owner_info.get('owner_username'):
            username = owner_info['owner_username']
            results.append({
                "nft_name": nft["name"],
                "url": url,
                "owner": username,
                "difficulty": nft.get("difficulty", "unknown")
            })
            logger.info(f"✅ Найден владелец: @{username}")
        
        used_ids.add(nft_id)
        attempts += 1
        await asyncio.sleep(0.2)
    
    return results

# ========== ПОКАЗ РЕЗУЛЬТАТОВ ==========
async def show_search_results(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    
    if not await require_subscription(update, context):
        return
    
    await query.message.edit_text(
        "╔══════════════════════════╗\n"
        "║     🔍 ПОИСК...          ║\n"
        "╚══════════════════════════╝\n\n"
        "⚡ Ищем владельцев NFT...\n"
        "⏳ Это займет 5-10 секунд"
    )
    
    results = await find_owners(5)
    
    if user_id in users_db:
        users_db[user_id]['searches'] += 1
        users_db[user_id]['found'] += len(results)
    
    if not results:
        keyboard = [[InlineKeyboardButton("🔄 ПОПРОБОВАТЬ СНОВА", callback_data="search")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.edit_text(
            "╔══════════════════════════╗\n"
            "║     ❌ НИЧЕГО НЕ НАЙДЕНО ║\n"
            "╚══════════════════════════╝\n\n"
            "Попробуйте еще раз позже.",
            reply_markup=reply_markup
        )
        return
    
    text = "╔══════════════════════════╗\n"
    text += "║     🎯 НАЙДЕНЫ ВЛАДЕЛЬЦЫ ║\n"
    text += "╚══════════════════════════╝\n\n"
    
    for i, item in enumerate(results, 1):
        text += f"{i}. 👤 @{item['owner']}\n"
        text += f"   🎁 {item['nft_name']} ({item['difficulty']})\n"
        text += f"   🔗 [Ссылка]({item['url']})\n\n"
    
    text += f"📊 Найдено: {len(results)} владельцев"
    
    keyboard = [
        [InlineKeyboardButton("🔄 НОВЫЙ ПОИСК", callback_data="search")],
        [InlineKeyboardButton("🏠 ГЛАВНОЕ МЕНЮ", callback_data="main_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.message.edit_text(
        text,
        reply_markup=reply_markup,
        parse_mode='Markdown',
        disable_web_page_preview=True
    )

# ========== ОБРАБОТЧИК МЕНЮ ==========
async def handle_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if not await require_subscription(update, context):
        return
    
    if query.data == "main_menu":
        await show_main_menu(update, context)
    elif query.data == "search":
        await show_search_results(update, context)

# ========== ЗАПУСК ==========
def main():
    print("╔════════════════════════════════════╗")
    print("║      🚀 NFT ПАРСЕР ЗАПУЩЕН        ║")
    print("╚════════════════════════════════════╝")
    print(f"📢 ID канала: {CHANNEL_ID}")
    print(f"🔗 Ссылка: {CHANNEL_LINK}")
    print(f"📊 NFT в базе: {len(NFT_LIST)}")
    print(f"🚫 В бане: {len(BANNED_USERNAMES)} ников")
    print("=" * 40)
    
    app = Application.builder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_menu))
    
    print("✅ Бот готов к работе!")
    app.run_polling()

if __name__ == "__main__":
    main()
