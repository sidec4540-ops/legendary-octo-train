import logging
import random
import re
import asyncio
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters
from telegram.constants import ParseMode

# ========== ТВОИ ДАННЫЕ ==========
BOT_TOKEN = "8430585997:AAFE8C3ostnoTQiwSlwVmYpnVQI5FjbsCRc"
CHANNEL_LINK = "https://t.me/+WLiiYR7_ymZjYWY1"
CHANNEL_ID = -1003256576224
YOUR_TELEGRAM_ID = 571001160

# ========== БАН-ЛИСТ (РЕЛЕИ И МУСОР) ==========
BANNED_USERNAMES = {
    "giftrelayer", "mrktbank", "kallent", "monk", "durov",
    "virusgift", "portalsrelayer", "lucha", "snoopdogg", "snoop", 
    "ufc", "nft", "telegram", "nftgift", "nftgiftbot", "ton", "gift",
    "relayer", "bank", "kallen", "nftbot", "giftbot", "channel", "nftrelayer",
    "nftcollector", "nftmarket", "nfttrade", "nftshop", "nftstore",
    "sale", "market", "auction", "bid", "trade", "exchange"
}

# ========== НАСТРОЙКИ ==========
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ========== ХРАНИЛИЩЕ ==========
users_db = {}
user_settings = {}
last_message_ids = {}

# ========== ПОЛНЫЙ СПИСОК NFT ==========
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

# ========== ФУНКЦИЯ ПАРСИНГА ВЛАДЕЛЬЦА ==========
def extract_owner_from_nft(gift_url: str) -> str | None:
    """
    Парсит страницу NFT и возвращает @username владельца.
    Если владельца нет или это релей — возвращает None.
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(gift_url, headers=headers, timeout=5)
        
        if response.status_code != 200:
            return None
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 1. Проверяем data-user атрибуты
        data_elements = soup.find_all(attrs={'data-user': True})
        for elem in data_elements:
            user_data = elem.get('data-user', '')
            if user_data:
                # Пробуем найти username в JSON
                username_match = re.search(r'"username"\s*:\s*"@?(\w{5,32})"', user_data)
                if username_match:
                    username = username_match.group(1).lower()
                    if username not in BANNED_USERNAMES:
                        return username
                
                # Просто @username
                username_match = re.search(r'@(\w{5,32})', user_data)
                if username_match:
                    username = username_match.group(1).lower()
                    if username not in BANNED_USERNAMES:
                        return username
        
        # 2. Ищем в meta-тегах (og:description)
        meta_desc = soup.find('meta', property='og:description')
        if meta_desc and meta_desc.get('content'):
            content = meta_desc['content']
            username_match = re.search(r'@(\w{5,32})', content)
            if username_match:
                username = username_match.group(1).lower()
                if username not in BANNED_USERNAMES:
                    return username
        
        # 3. Ищем в скриптах с initData
        script_tags = soup.find_all('script')
        for script in script_tags:
            content = script.string or ''
            if 'initData' in content or 'user' in content:
                username_match = re.search(r'"username"\s*:\s*"@?(\w{5,32})"', content)
                if username_match:
                    username = username_match.group(1).lower()
                    if username not in BANNED_USERNAMES:
                        return username
                
                # Прямой @username
                username_match = re.search(r'@(\w{5,32})', content)
                if username_match:
                    username = username_match.group(1).lower()
                    if username not in BANNED_USERNAMES:
                        return username
        
        # 4. Ищем в тексте страницы
        page_text = soup.get_text()
        usernames = re.findall(r'@(\w{5,32})', page_text)
        
        # Фильтруем мусор
        filtered = [u for u in usernames if u.lower() not in 
                   ['telegram', 'nft', 'gift', 'bot', 'admin', 'support', 'channel']]
        
        for username in filtered:
            if username.lower() not in BANNED_USERNAMES:
                return username.lower()
        
        return None
        
    except Exception as e:
        logger.error(f"Ошибка парсинга {gift_url}: {e}")
        return None

# ========== ФУНКЦИЯ ПОИСКА РЕАЛЬНЫХ ВЛАДЕЛЬЦЕВ ==========
async def find_real_owners(count=5):
    """
    Генерирует РАНДОМНЫЕ числа в диапазоне каждого NFT,
    парсит страницу, проверяет бан-лист,
    возвращает ТОЛЬКО те, у которых есть реальный владелец.
    """
    results = []
    used_ids = set()  # чтобы не повторяться
    attempts = 0
    max_attempts = 200  # максимум попыток, чтобы не зависнуть
    
    while len(results) < count and attempts < max_attempts:
        # Берём случайный NFT из списка
        nft = random.choice(NFT_LIST)
        
        # Генерируем РАНДОМНОЕ ЧИСЛО в его диапазоне
        nft_id = random.randint(nft["min_id"], nft["max_id"])
        
        # Проверяем, не использовали ли уже этот ID
        if nft_id in used_ids:
            attempts += 1
            continue
        
        # Формируем URL
        clean_name = re.sub(r"[^\w]", "", nft["name"])
        url = f"https://t.me/nft/{clean_name}-{nft_id}"
        
        # Парсим страницу и пытаемся найти владельца
        username = extract_owner_from_nft(url)
        
        # Если нашли владельца и он не в бане — добавляем в результаты
        if username:
            results.append({
                "name": nft["name"],
                "url": url,
                "username": username,
                "difficulty": nft.get("difficulty", "unknown"),
                "id": nft_id
            })
            logger.info(f"✅ Найден реальный владелец: @{username} (ID: {nft_id})")
        
        # Запоминаем ID, чтобы не повторяться
        used_ids.add(nft_id)
        attempts += 1
        
        # Небольшая задержка, чтобы не заблокировали
        await asyncio.sleep(0.2)
    
    logger.info(f"🎯 Найдено {len(results)} реальных владельцев за {attempts} попыток")
    return results

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

# ========== ГЛАВНОЕ МЕНЮ ==========
async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    
    text = f"❗ Привет, @{user.username or 'user'}! Это парсер для поиска мамонтов."
    
    keyboard = [
        [InlineKeyboardButton("🔍 Поиск владельцев", callback_data="search")],
        [InlineKeyboardButton("👤 Мой профиль", callback_data="menu_profile")],
        [InlineKeyboardButton("📢 Канал", url=CHANNEL_LINK)]
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

# ========== ПРОФИЛЬ ==========
async def show_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    user = users_db.get(user_id, {})
    
    text = f"""ID: {user_id}
Имя: @{user.get('username', 'unknown')}
Дата регистрации: {user.get('registered', 'Неизвестно')}

СТАТИСТИКА
Всего поисков: {user.get('searches', 0)}
Найдено владельцев: {user.get('found', 0)}"""
    
    keyboard = [[InlineKeyboardButton("◀️ Назад", callback_data="main_menu")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.message.edit_text(text, reply_markup=reply_markup)

# ========== ПОКАЗ РЕЗУЛЬТАТОВ ==========
async def show_search_results(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    
    if not await require_subscription(update, context):
        return
    
    await query.message.edit_text("🔍 Ищу реальных владельцев NFT... Это может занять до 30 секунд")
    
    results = await find_real_owners(5)
    
    if user_id in users_db:
        users_db[user_id]['searches'] += 1
        users_db[user_id]['found'] += len(results)
    
    if not results:
        keyboard = [[InlineKeyboardButton("🔄 Попробовать снова", callback_data="search")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.edit_text(
            "❌ Не найдено реальных владельцев.\nПопробуйте еще раз.",
            reply_markup=reply_markup
        )
        return
    
    text = "*Найденные владельцы:*\n\n"
    for i, item in enumerate(results, 1):
        text += f"{i}. 👤 @{item['username']}\n"
        text += f"   🎁 {item['name']} ({item['difficulty']})\n"
        text += f"   🔗 [Ссылка]({item['url']})\n\n"
    
    text += f"📊 Найдено: {len(results)} владельцев"
    
    keyboard = [
        [InlineKeyboardButton("🔄 Новый поиск", callback_data="search")],
        [InlineKeyboardButton("◀️ Главное меню", callback_data="main_menu")]
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
    elif query.data == "menu_profile":
        await show_profile(update, context)

# ========== ЗАПУСК ==========
def main():
    print("=" * 50)
    print("🤖 NFT ПАРСЕР ЗАПУЩЕН")
    print("=" * 50)
    print(f"📢 ID канала: {CHANNEL_ID}")
    print(f"📊 NFT в базе: {len(NFT_LIST)}")
    print(f"🚫 В бане: {len(BANNED_USERNAMES)} ников")
    print("=" * 50)
    
    app = Application.builder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_menu))
    
    print("✅ Бот готов к работе!")
    app.run_polling()

if __name__ == "__main__":
    main()