import logging
import random
import re
import requests
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters
from telegram.constants import ParseMode

# ========== ТВОИ ДАННЫЕ ==========
BOT_TOKEN = "8430585997:AAFE8C3ostnoTQiwSlwVmYpnVQI5FjbsCRc"
CHANNEL_LINK = "https://t.me/+WLiiYR7_ymZjYWY1"
CHANNEL_ID = -1003256576224
YOUR_TELEGRAM_ID = 571001160

# ========== БАН-ЛИСТ (РЕЛЕИ, КРУПНЯК, БОТЫ) ==========
BANNED_USERNAMES = {
    "giftrelayer", "mrktbank", "kallent", "monk", "durov",
    "virusgift", "portalsrelayer", "lucha", "snoopdogg", "snoop", 
    "ufc", "nft", "telegram", "nftgift", "nftgiftbot", "ton", "gift",
    "relayer", "bank", "kallen", "nftbot", "giftbot", "channel", "group"
}
BANNED_IDS = set()

# ========== ЖЕНСКИЕ ИМЕНА ==========
FEMALE_NAMES = {
    "anna", "anya", "maria", "masha", "olga", "olya", "katya", "kate", "ekaterina",
    "nastya", "nastia", "dasha", "daria", "sveta", "svetlana", "lena", "elena", 
    "alena", "alina", "yana", "vika", "viktoria", "kristina", "kris", "ksenia",
    "анна", "аня", "мария", "маша", "ольга", "оля", "катя", "екатерина",
    "настя", "настасья", "даша", "дарья", "света", "светлана", "лена", "елена",
    "алена", "алина", "яна", "вика", "виктория", "кристина", "ксения", "полина",
    "поля", "софия", "соня", "софья", "татьяна", "таня", "ирина", "ира"
}

# ========== НАСТРОЙКИ ==========
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ========== ПОЛНЫЙ СПИСОК NFT ==========
NFT_LIST = [
    {"name": "BDayCandle", "difficulty": "easy", "min_id": 1000, "max_id": 20000},
    {"name": "CandyCane", "difficulty": "easy", "min_id": 1000, "max_id": 150000},
    {"name": "CloverPin", "difficulty": "easy", "min_id": 1000, "max_id": 60000},
    {"name": "CookieHeart", "difficulty": "medium", "min_id": 1000, "max_id": 60000},
    {"name": "EasterEgg", "difficulty": "medium", "min_id": 1000, "max_id": 60000},
    {"name": "GingerCookie", "difficulty": "easy", "min_id": 1000, "max_id": 60000},
    {"name": "HeartLocket", "difficulty": "hard", "min_id": 1000, "max_id": 60000},
    {"name": "LoveCandle", "difficulty": "hard", "min_id": 1000, "max_id": 60000},
    {"name": "LovePotion", "difficulty": "hard", "min_id": 1000, "max_id": 60000},
    {"name": "Rose", "difficulty": "medium", "min_id": 1000, "max_id": 60000},
    {"name": "SweetCookie", "difficulty": "easy", "min_id": 1000, "max_id": 60000},
    {"name": "BunnyMuffin", "difficulty": "medium", "min_id": 1000, "max_id": 60000},
    {"name": "Cherry", "difficulty": "easy", "min_id": 1000, "max_id": 60000},
    {"name": "KissedFrog", "difficulty": "hard", "min_id": 1000, "max_id": 60000},
    {"name": "Peach", "difficulty": "easy", "min_id": 1000, "max_id": 60000},
]

NFT_DICT = {nft["name"]: nft for nft in NFT_LIST}

# ========== ХРАНИЛИЩЕ ==========
users_db = {}
blocked_nfts = {}
user_settings = {}
last_message_ids = {}

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
    message = "╔══════════════════════════╗\n║     ⚠️ ПОДПИСКА         ║\n╚══════════════════════════╝\n\nДля использования бота подпишитесь на канал!"
    
    if update.callback_query:
        await update.callback_query.message.edit_text(message, reply_markup=reply_markup)
    else:
        await update.message.reply_text(message, reply_markup=reply_markup)

# ========== ФУНКЦИЯ ПОИСКА ВЛАДЕЛЬЦА NFT ==========
def get_nft_owner(gift_url: str) -> dict:
    """Парсит страницу NFT и возвращает информацию о владельце"""
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(gift_url, headers=headers, timeout=5)
        
        if response.status_code != 200:
            return {'success': False, 'error': f'HTTP {response.status_code}'}
        
        text = response.text
        
        # Ищем username в тексте
        username_match = re.search(r'@(\w{5,32})', text)
        if username_match:
            username = username_match.group(1).lower()
            return {
                'success': True,
                'owner_username': username,
                'owner_id': None,
                'url': gift_url
            }
        
        return {'success': False, 'error': 'Владелец не найден'}
        
    except Exception as e:
        logger.error(f"Ошибка парсинга {gift_url}: {e}")
        return {'success': False, 'error': str(e)}

# ========== ФУНКЦИЯ ГЕНЕРАЦИИ NFT С ПОИСКОМ ВЛАДЕЛЬЦЕВ ==========
async def find_nft_with_owners(count=5, mode="girls"):
    """Генерирует NFT и возвращает только те, у которых есть владелец"""
    
    # Фильтруем NFT по режиму
    if mode == "girls":
        girl_keywords = ["heart", "love", "rose", "sweet", "bunny", "cookie", "cherry", "kiss", "peach"]
        available_nfts = [n for n in NFT_LIST if any(k in n["name"].lower() for k in girl_keywords)]
    elif mode == "light":
        available_nfts = [n for n in NFT_LIST if n["difficulty"] == "easy"]
    elif mode == "medium":
        available_nfts = [n for n in NFT_LIST if n["difficulty"] in ["easy", "medium"]]
    elif mode == "heavy":
        available_nfts = [n for n in NFT_LIST if n["difficulty"] in ["medium", "hard"]]
    else:
        available_nfts = NFT_LIST
    
    if not available_nfts:
        available_nfts = NFT_LIST
    
    results = []
    used_ids = set()
    attempts = 0
    max_attempts = 50
    
    while len(results) < count and attempts < max_attempts:
        nft = random.choice(available_nfts)
        nft_id = random.randint(nft["min_id"], nft["max_id"])
        
        if nft_id in used_ids:
            attempts += 1
            continue
        
        clean_name = re.sub(r"[^\w]", "", nft["name"])
        url = f"https://t.me/nft/{clean_name}-{nft_id}"
        
        # Получаем информацию о владельце
        owner_info = get_nft_owner(url)
        
        if owner_info['success'] and owner_info.get('owner_username'):
            username = owner_info['owner_username']
            
            # Проверяем бан-лист
            if username not in BANNED_USERNAMES:
                # Для режима "girls" проверяем женские имена
                if mode == "girls":
                    is_female = any(name in username for name in FEMALE_NAMES)
                    if is_female:
                        results.append({
                            "name": nft["name"],
                            "url": url,
                            "owner": username,
                            "nft_id": nft_id
                        })
                        logger.info(f"✅ Найдена девушка: @{username}")
                else:
                    # Для других режимов добавляем всех, кроме бана
                    results.append({
                        "name": nft["name"],
                        "url": url,
                        "owner": username,
                        "nft_id": nft_id
                    })
                    logger.info(f"✅ Найден владелец: @{username}")
        
        used_ids.add(nft_id)
        attempts += 1
    
    logger.info(f"🎯 Найдено {len(results)} владельцев за {attempts} попыток")
    return results

# ========== ГЛАВНОЕ МЕНЮ ==========
async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    
    text = "╔══════════════════════════╗\n"
    text += "║     🚀 NFT ПАРСЕР       ║\n"
    text += "╚══════════════════════════╝\n\n"
    text += f"👋 Привет, @{user.username or 'user'}!\n\n"
    text += "🔍 Поиск владельцев NFT\n"
    text += "🚫 Бан-лист релеев и ботов\n"
    text += "👧 Фильтр по женским именам"
    
    keyboard = [
        [InlineKeyboardButton("👧 ПОИСК ДЕВУШЕК", callback_data="search_girls")],
        [InlineKeyboardButton("🎲 РАНДОМ ПОИСК", callback_data="search_random")],
        [InlineKeyboardButton("👤 МОЙ ПРОФИЛЬ", callback_data="menu_profile")],
        [InlineKeyboardButton("📢 КАНАЛ", url=CHANNEL_LINK)]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.callback_query:
        await update.callback_query.message.edit_text(text, reply_markup=reply_markup, parse_mode='Markdown')
    else:
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')

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
            'users_found': 0
        }
    
    if user_id not in user_settings:
        user_settings[user_id] = {'results_count': 5}
    
    await show_main_menu(update, context)

# ========== МЕНЮ ПОИСКА ==========
async def show_search_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    
    text = "╔══════════════════════════╗\n"
    text += "║     🔍 ВЫБОР ПОИСКА     ║\n"
    text += "╚══════════════════════════╝\n\n"
    text += "👧 Поиск девушек - только женские ники\n"
    text += "🎲 Рандом поиск - все владельцы (кроме бана)"
    
    keyboard = [
        [InlineKeyboardButton("👧 ПОИСК ДЕВУШЕК", callback_data="search_girls")],
        [InlineKeyboardButton("🎲 РАНДОМ ПОИСК", callback_data="search_random")],
        [InlineKeyboardButton("◀️ НАЗАД", callback_data="main_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.message.edit_text(text, reply_markup=reply_markup, parse_mode='Markdown')

# ========== МЕНЮ РЕЖИМОВ ==========
async def show_modes_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    
    text = "╔══════════════════════════╗\n"
    text += "║     🎲 ВЫБОР РЕЖИМА     ║\n"
    text += "╚══════════════════════════╝\n\n"
    text += "🟢 Легкий - дешевые подарки\n"
    text += "🟡 Средний - средние подарки\n"
    text += "🔴 Жирный - дорогие подарки"
    
    keyboard = [
        [InlineKeyboardButton("🟢 ЛЕГКИЙ РЕЖИМ", callback_data="mode_light")],
        [InlineKeyboardButton("🟡 СРЕДНИЙ РЕЖИМ", callback_data="mode_medium")],
        [InlineKeyboardButton("🔴 ЖИРНЫЙ РЕЖИМ", callback_data="mode_heavy")],
        [InlineKeyboardButton("◀️ НАЗАД", callback_data="menu_search")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.message.edit_text(text, reply_markup=reply_markup, parse_mode='Markdown')

# ========== ПОИСК И ПОКАЗ РЕЗУЛЬТАТОВ ==========
async def start_search(update: Update, context: ContextTypes.DEFAULT_TYPE, mode):
    query = update.callback_query
    user_id = query.from_user.id
    
    # Сообщение о начале поиска
    await query.message.edit_text(
        "╔══════════════════════════╗\n"
        "║     🔍 ПОИСК...          ║\n"
        "╚══════════════════════════╝\n\n"
        "⚡ Ищем владельцев NFT...\n"
        "⏳ Это займет 5-10 секунд",
        parse_mode='Markdown'
    )
    
    # Запускаем поиск
    results = await find_nft_with_owners(5, mode)
    
    # Обновляем статистику
    if user_id in users_db:
        users_db[user_id]['searches'] += 1
        users_db[user_id]['users_found'] += len(results)
    
    if not results:
        keyboard = [[InlineKeyboardButton("🔄 ПОПРОБОВАТЬ СНОВА", callback_data=f"search_{mode}")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.edit_text(
            "╔══════════════════════════╗\n"
            "║     ❌ НИЧЕГО НЕ НАЙДЕНО ║\n"
            "╚══════════════════════════╝\n\n"
            "Попробуйте еще раз позже.",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        return
    
    # Формируем результат
    text = "╔══════════════════════════╗\n"
    text += "║     🎯 РЕЗУЛЬТАТЫ       ║\n"
    text += "╚══════════════════════════╝\n\n"
    
    for i, item in enumerate(results, 1):
        text += f"{i}. 👤 @{item['owner']}\n"
        text += f"   🎁 {item['name']}\n"
        text += f"   🔗 [Ссылка]({item['url']})\n\n"
    
    text += f"📊 Найдено: {len(results)} владельцев"
    
    keyboard = [
        [InlineKeyboardButton("🔄 НОВЫЙ ПОИСК", callback_data=f"search_{mode}")],
        [InlineKeyboardButton("🏠 ГЛАВНОЕ МЕНЮ", callback_data="main_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.message.edit_text(
        text,
        reply_markup=reply_markup,
        parse_mode='Markdown',
        disable_web_page_preview=True
    )

# ========== ПРОФИЛЬ ==========
async def show_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    user = users_db.get(user_id, {})
    
    text = "╔══════════════════════════╗\n"
    text += "║        👤 ПРОФИЛЬ        ║\n"
    text += "╚══════════════════════════╝\n\n"
    text += f"🆔 ID: `{user_id}`\n"
    text += f"👤 Username: @{user.get('username', 'unknown')}\n"
    text += f"📅 Регистрация: {user.get('registered', 'Неизвестно')}\n\n"
    text += f"📊 *Статистика*\n"
    text += f"├─ Поисков: {user.get('searches', 0)}\n"
    text += f"└─ Найдено: {user.get('users_found', 0)}"
    
    keyboard = [[InlineKeyboardButton("◀️ НАЗАД", callback_data="main_menu")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.message.edit_text(text, reply_markup=reply_markup, parse_mode='Markdown')

# ========== ОБРАБОТЧИК МЕНЮ ==========
async def handle_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if not await require_subscription(update, context):
        return
    
    data = query.data
    
    if data == "main_menu":
        await show_main_menu(update, context)
    elif data == "menu_profile":
        await show_profile(update, context)
    elif data == "menu_search":
        await show_search_menu(update, context)
    elif data == "search_random":
        await show_modes_menu(update, context)
    elif data == "search_girls":
        await start_search(update, context, "girls")
    elif data == "mode_light":
        await start_search(update, context, "light")
    elif data == "mode_medium":
        await start_search(update, context, "medium")
    elif data == "mode_heavy":
        await start_search(update, context, "heavy")

# ========== HELP КОМАНДА ==========
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await require_subscription(update, context):
        return
    
    text = "🆘 *СПРАВКА*\n\n"
    text += "/start - Начать работу\n"
    text += "/help - Это сообщение"
    
    await update.message.reply_text(text, parse_mode='Markdown')

# ========== ЗАПУСК БОТА ==========
def main():
    print("╔════════════════════════════════════╗")
    print("║      🚀 NFT ПАРСЕР ЗАПУЩЕН        ║")
    print("╚════════════════════════════════════╝")
    print(f"📢 ID канала: {CHANNEL_ID}")
    print(f"🔗 Ссылка: {CHANNEL_LINK}")
    print(f"🚫 В бане: {len(BANNED_USERNAMES)} ников")
    print("=" * 40)
    
    app = Application.builder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CallbackQueryHandler(handle_menu))
    
    print("✅ Бот готов к работе!")
    app.run_polling()

if __name__ == "__main__":
    main()
