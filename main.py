import logging
import random
import re
import time
import asyncio
import aiohttp
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters
from telegram.constants import ParseMode
from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache
from bs4 import BeautifulSoup

# ========== ТВОИ ДАННЫЕ ==========
BOT_TOKEN = "8616937683:AAGSWcZhZWgdBx4y28IhK7Y7kXLab8IrbL0"
CHANNEL_LINK = "https://t.me/+i6Zr8Mk_fYYxMTI0"
CHANNEL_ID = -1003885502543
YOUR_TELEGRAM_ID = 571001160

# ========== БАН-ЛИСТ ==========
BANNED_USERNAMES = {
    "giftrelayer", "mrktbank", "kallent", "monk", "durov",
    "virusgift", "portalsrelayer", "lucha", "snoopdogg", "snoop", 
    "ufc", "nft", "telegram"
}

# ========== ЖЕНСКИЕ ИМЕНА ==========
FEMALE_NAMES = {
    "anna", "anya", "maria", "masha", "olga", "olya", "katya", "kate",
    "nastya", "dasha", "sveta", "lena", "alena", "yana", "vika", "nastia",
    "анна", "аня", "маша", "катя", "настя", "даша", "света", "лена"
}

# ========== НАСТРОЙКИ ==========
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ========== КЭШ ДЛЯ ПАРСИНГА ==========
parser_cache = {}
cache_ttl = 3600  # 1 час

# ========== ПОЛНЫЙ СПИСОК NFT ==========
NFT_LIST = [
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
    keyboard = [[InlineKeyboardButton("📢 Подписаться", url=CHANNEL_LINK)]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    message = "⚠️ Для использования бота подпишитесь на канал!"
    
    if update.callback_query:
        await update.callback_query.message.edit_text(message, reply_markup=reply_markup)
    else:
        await update.message.reply_text(message, reply_markup=reply_markup)

# ========== БЫСТРЫЙ ПАРСИНГ С КЭШЕМ ==========
async def quick_parse_nft(session: aiohttp.ClientSession, gift_url: str) -> dict:
    """Быстрый парсинг страницы NFT с кэшированием"""
    
    # Проверяем кэш
    if gift_url in parser_cache:
        cache_time, result = parser_cache[gift_url]
        if time.time() - cache_time < cache_ttl:
            return result
    
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        async with session.get(gift_url, headers=headers, timeout=3) as response:
            if response.status != 200:
                return None
            
            html = await response.text()
            soup = BeautifulSoup(html, 'html.parser')
            
            # Ищем username
            text = soup.get_text()
            username_match = re.search(r'@(\w{5,32})', text)
            
            result = None
            if username_match:
                username = username_match.group(1).lower()
                if username not in BANNED_USERNAMES:
                    # Проверяем на женское имя
                    is_female = any(name in username for name in FEMALE_NAMES)
                    if is_female:
                        result = {
                            'username': username,
                            'url': gift_url,
                            'success': True
                        }
            
            # Сохраняем в кэш
            parser_cache[gift_url] = (time.time(), result)
            return result
            
    except Exception as e:
        logger.error(f"Ошибка парсинга {gift_url}: {e}")
        parser_cache[gift_url] = (time.time(), None)
        return None

# ========== ПАРАЛЛЕЛЬНЫЙ ПОИСК ==========
async def parallel_search(count=10):
    """Параллельный поиск NFT с быстрым парсингом"""
    
    girl_nfts = [n for n in NFT_LIST if any(word in n["name"].lower() for word in 
                 ["heart", "love", "rose", "sweet", "bunny", "cookie", "cherry", "kiss"])]
    
    if not girl_nfts:
        girl_nfts = NFT_LIST
    
    results = []
    used_ids = set()
    attempts = 0
    max_attempts = 100
    
    # Создаем сессию для параллельных запросов
    async with aiohttp.ClientSession() as session:
        tasks = []
        
        while len(results) < count and attempts < max_attempts:
            nft = random.choice(girl_nfts)
            nft_id = random.randint(nft["min_id"], nft["max_id"])
            
            if nft_id in used_ids:
                attempts += 1
                continue
            
            clean_name = re.sub(r"[^\w]", "", nft["name"])
            url = f"https://t.me/nft/{clean_name}-{nft_id}"
            
            # Добавляем задачу на парсинг
            tasks.append(quick_parse_nft(session, url))
            used_ids.add(nft_id)
            attempts += 1
            
            # Каждые 10 задач обрабатываем результаты
            if len(tasks) >= 10 or len(results) >= count:
                parsed_results = await asyncio.gather(*tasks)
                for res in parsed_results:
                    if res and len(results) < count:
                        results.append(res)
                tasks = []
    
    return results[:count]

# ========== КРАСИВЫЙ ВЫВОД РЕЗУЛЬТАТОВ ==========
async def show_beautiful_results(update: Update, context: ContextTypes.DEFAULT_TYPE, page=1):
    query = update.callback_query
    user_id = query.from_user.id
    
    # Сообщение о начале поиска
    await query.message.edit_text("🔍 *Поиск девушек в NFT...*\n\n⏳ Это займет около 10-15 секунд", parse_mode='Markdown')
    
    # Параллельный поиск
    girls = await parallel_search(10)
    
    if not girls:
        keyboard = [[InlineKeyboardButton("🔄 Попробовать снова", callback_data="search_girls")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.edit_text(
            "❌ *Никого не нашлось*\n\nПопробуйте еще раз через несколько минут.",
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
        return
    
    # Пагинация
    items_per_page = 5
    total_pages = (len(girls) + items_per_page - 1) // items_per_page
    start = (page - 1) * items_per_page
    end = min(start + items_per_page, len(girls))
    page_girls = girls[start:end]
    
    # Красивый заголовок
    text = "╔══════════════════════════╗\n"
    text += "║     🎯 НАЙДЕННЫЕ NFT     ║\n"
    text += "╚══════════════════════════╝\n\n"
    
    # Список с красивым форматированием
    for i, girl in enumerate(page_girls, start=start + 1):
        text += f"┌─ #{i}\n"
        text += f"├─ 👤 @{girl['username']}\n"
        text += f"└─ 🔗 [Открыть NFT]({girl['url']})\n\n"
    
    text += f"📊 *Всего найдено:* {len(girls)}\n"
    text += f"📄 *Страница:* {page}/{total_pages}"
    
    # Кнопки навигации
    keyboard = []
    
    if total_pages > 1:
        nav_row = []
        if page > 1:
            nav_row.append(InlineKeyboardButton("◀️ Назад", callback_data=f"girls_page_{page-1}"))
        nav_row.append(InlineKeyboardButton(f"{page}/{total_pages}", callback_data="noop"))
        if page < total_pages:
            nav_row.append(InlineKeyboardButton("Вперед ▶️", callback_data=f"girls_page_{page+1}"))
        keyboard.append(nav_row)
    
    keyboard.append([InlineKeyboardButton("🔄 Новый поиск", callback_data="search_girls")])
    keyboard.append([InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.message.edit_text(
        text,
        reply_markup=reply_markup,
        parse_mode='Markdown',
        disable_web_page_preview=True
    )

# ========== ГЛАВНОЕ МЕНЮ ==========
async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    
    text = "╔══════════════════════════╗\n"
    text += "║     🤖 NFT ПАРСЕР БОТ    ║\n"
    text += "╚══════════════════════════╝\n\n"
    text += f"👋 Привет, @{user.username or 'user'}!\n\n"
    text += "🔍 Ищу девушек в NFT-подарках Telegram\n"
    text += "⚡ Быстрый параллельный парсинг\n"
    text += "🎯 Только реальные пользователи"
    
    keyboard = [
        [InlineKeyboardButton("🔍 Найти девушек", callback_data="search_girls")],
        [InlineKeyboardButton("👤 Мой профиль", callback_data="menu_profile")],
        [InlineKeyboardButton("⚙️ Настройки", callback_data="menu_settings")],
        [InlineKeyboardButton("📢 Канал", url=CHANNEL_LINK)]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.callback_query:
        await update.callback_query.message.edit_text(text, reply_markup=reply_markup, parse_mode='Markdown')
    else:
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')

# ========== START ==========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if not await require_subscription(update, context):
        return
    
    if user_id not in users_db:
        users_db[user_id] = {
            'username': update.effective_user.username or f"user{user_id}",
            'registered': datetime.now().strftime("%Y-%m-%d"),
            'searches': 0
        }
    
    await show_main_menu(update, context)

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
    text += f"└─ Блокировок: {len(blocked_nfts.get(user_id, []))}"
    
    keyboard = [[InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.message.edit_text(text, reply_markup=reply_markup, parse_mode='Markdown')

# ========== НАСТРОЙКИ ==========
async def show_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    
    text = "╔══════════════════════════╗\n"
    text += "║       ⚙️ НАСТРОЙКИ       ║\n"
    text += "╚══════════════════════════╝\n\n"
    text += "Раздел в разработке"
    
    keyboard = [[InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.message.edit_text(text, reply_markup=reply_markup, parse_mode='Markdown')

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
    elif data == "menu_profile":
        await show_profile(update, context)
    elif data == "menu_settings":
        await show_settings(update, context)
    elif data == "search_girls":
        await show_beautiful_results(update, context, 1)
    elif data.startswith("girls_page_"):
        page = int(data.split("_")[2])
        await show_beautiful_results(update, context, page)
    elif data == "noop":
        pass

# ========== HELP ==========
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await require_subscription(update, context):
        return
    
    text = "🆘 *СПРАВКА*\n\n"
    text += "/start - Начать работу\n"
    text += "/help - Это сообщение"
    
    await update.message.reply_text(text, parse_mode='Markdown')

# ========== ЗАПУСК ==========
def main():
    print("╔════════════════════════════════════╗")
    print("║      🚀 NFT ПАРСЕР БОТ СТАРТ      ║")
    print("╚════════════════════════════════════╝")
    print(f"📢 ID канала: {CHANNEL_ID}")
    print(f"🔗 Ссылка: {CHANNEL_LINK}")
    print("⚡ Быстрый параллельный парсинг")
    print("🎨 Красивое оформление")
    print("=" * 40)
    
    app = Application.builder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CallbackQueryHandler(handle_menu))
    
    print("✅ Бот готов к работе!")
    app.run_polling()

if __name__ == "__main__":
    main()
    
