import logging
import random
import re
import time
import json
import asyncio
import aiohttp
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from telegram.constants import ParseMode

# ========== ТВОИ ДАННЫЕ ==========
BOT_TOKEN = "8430585997:AAFE8C3ostnoTQiwSlwVmYpnVQI5FjbsCRc"
CHANNEL_LINK = "https://t.me/+WLiiYR7_ymZjYWY1"
CHANNEL_ID = -1003256576224

# ========== БАН-ЛИСТ ==========
BANNED_USERNAMES = {
    "giftrelayer", "mrktbank", "kallent", "monk", "durov",
    "virusgift", "portalsrelayer", "lucha", "snoopdogg", "snoop", 
    "ufc", "nft", "telegram", "nftgift", "nftgiftbot", "ton", "gift",
    "relayer", "bank", "kallen"
}

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
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ========== КЭШ ДЛЯ БЫСТРОГО ПАРСИНГА ==========
parser_cache = {}
cache_ttl = 3600  # 1 час

# ========== ОПТИМИЗИРОВАННЫЙ СПИСОК NFT ==========
NFT_LIST = [
    {"name": "CandyCane", "min_id": 1000, "max_id": 150000},
    {"name": "CloverPin", "min_id": 1000, "max_id": 60000},
    {"name": "CookieHeart", "min_id": 1000, "max_id": 60000},
    {"name": "EasterEgg", "min_id": 1000, "max_id": 60000},
    {"name": "GingerCookie", "min_id": 1000, "max_id": 60000},
    {"name": "HeartLocket", "min_id": 1000, "max_id": 60000},
    {"name": "LoveCandle", "min_id": 1000, "max_id": 60000},
    {"name": "LovePotion", "min_id": 1000, "max_id": 60000},
    {"name": "Rose", "min_id": 1000, "max_id": 60000},
    {"name": "SweetCookie", "min_id": 1000, "max_id": 60000},
    {"name": "BunnyMuffin", "min_id": 1000, "max_id": 60000},
    {"name": "Cherry", "min_id": 1000, "max_id": 60000},
    {"name": "KissedFrog", "min_id": 1000, "max_id": 60000},
    {"name": "Peach", "min_id": 1000, "max_id": 60000},
    {"name": "BerryBox", "min_id": 1000, "max_id": 60000},
    {"name": "Bunny", "min_id": 1000, "max_id": 60000},
    {"name": "Cake", "min_id": 1000, "max_id": 130000},
    {"name": "Candle", "min_id": 1000, "max_id": 20000},
    {"name": "Chocolate", "min_id": 1000, "max_id": 60000},
]

# ========== ХРАНИЛИЩЕ ==========
users_db = {}
user_settings = {}

# ========== ПРОВЕРКА ПОДПИСКИ ==========
async def check_subscription(user_id: int, context: ContextTypes.DEFAULT_TYPE) -> bool:
    try:
        member = await context.bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        return member.status not in ["left", "kicked"]
    except Exception as e:
        logger.error(f"Ошибка проверки подписки: {e}")
        return False

# ========== СУПЕР-БЫСТРЫЙ ПАРСИНГ (АСИНХРОННЫЙ) ==========
async def quick_parse_owner(session: aiohttp.ClientSession, gift_url: str) -> dict:
    """Максимально быстрый парсинг с кэшем"""
    
    # Проверяем кэш
    if gift_url in parser_cache:
        cache_time, result = parser_cache[gift_url]
        if time.time() - cache_time < cache_ttl:
            return result
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml',
            'Accept-Language': 'ru-RU,ru;q=0.9',
            'Connection': 'keep-alive',
        }
        
        async with session.get(gift_url, headers=headers, timeout=3) as response:
            if response.status != 200:
                parser_cache[gift_url] = (time.time(), None)
                return None
            
            html = await response.text()
            
            # Ищем username в тексте (самый быстрый способ)
            username_match = re.search(r'@(\w{5,32})', html)
            
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
        logger.error(f"Ошибка парсинга: {e}")
        parser_cache[gift_url] = (time.time(), None)
        return None

# ========== ПАРАЛЛЕЛЬНЫЙ ПОИСК (10 ЗАПРОСОВ ОДНОВРЕМЕННО) ==========
async def parallel_search(count=10):
    """Параллельный поиск NFT (очень быстро)"""
    
    results = []
    used_ids = set()
    
    async with aiohttp.ClientSession() as session:
        tasks = []
        nft_list = []
        
        # Генерируем URL для проверки
        for _ in range(count * 3):  # Запас для отсева
            nft = random.choice(NFT_LIST)
            nft_id = random.randint(nft["min_id"], nft["max_id"])
            
            if nft_id in used_ids:
                continue
                
            clean_name = re.sub(r"[^\w]", "", nft["name"])
            url = f"https://t.me/nft/{clean_name}-{nft_id}"
            
            nft_list.append(url)
            used_ids.add(nft_id)
        
        # Запускаем ВСЕ запросы параллельно
        tasks = [quick_parse_owner(session, url) for url in nft_list]
        parsed_results = await asyncio.gather(*tasks)
        
        # Собираем только успешные результаты
        for res in parsed_results:
            if res and len(results) < count:
                results.append(res)
    
    return results

# ========== КРАСИВЫЙ ВЫВОД ==========
async def show_results(update: Update, context: ContextTypes.DEFAULT_TYPE, page=1):
    query = update.callback_query
    user_id = query.from_user.id
    
    # Проверяем подписку
    if not await check_subscription(user_id, context):
        keyboard = [[InlineKeyboardButton("📢 Подписаться", url=CHANNEL_LINK)]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.edit_text("⚠️ Сначала подпишись на канал!", reply_markup=reply_markup)
        return
    
    # Сообщение о начале поиска
    await query.message.edit_text(
        "🔍 *Активный поиск владельцев NFT...*\n\n"
        "⚡ Параллельный парсинг\n"
        "⏳ Ожидайте 5-10 секунд",
        parse_mode='Markdown'
    )
    
    # Запускаем параллельный поиск
    girls = await parallel_search(10)
    
    if not girls:
        keyboard = [[InlineKeyboardButton("🔄 Попробовать снова", callback_data="search")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.edit_text(
            "❌ *Никого не нашлось*\n\n"
            "Попробуйте еще раз через несколько секунд.",
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
    text += "║     🎯 ВЛАДЕЛЬЦЫ NFT     ║\n"
    text += "╚══════════════════════════╝\n\n"
    
    # Список с найденными
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
            nav_row.append(InlineKeyboardButton("◀️ Назад", callback_data=f"page_{page-1}"))
        nav_row.append(InlineKeyboardButton(f"📄 {page}/{total_pages}", callback_data="noop"))
        if page < total_pages:
            nav_row.append(InlineKeyboardButton("Вперед ▶️", callback_data=f"page_{page+1}"))
        keyboard.append(nav_row)
    
    keyboard.append([InlineKeyboardButton("🔄 Новый поиск", callback_data="search")])
    keyboard.append([InlineKeyboardButton("📢 Канал", url=CHANNEL_LINK)])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.message.edit_text(
        text,
        reply_markup=reply_markup,
        parse_mode='Markdown',
        disable_web_page_preview=True
    )

# ========== КОМАНДА START ==========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    username = update.effective_user.username or "друг"
    
    # Сохраняем пользователя
    if user_id not in users_db:
        users_db[user_id] = {
            'username': username,
            'registered': datetime.now().strftime("%Y-%m-%d"),
            'searches': 0
        }
    
    # Проверяем подписку
    if not await check_subscription(user_id, context):
        keyboard = [[InlineKeyboardButton("📢 Подписаться", url=CHANNEL_LINK)]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            "╔══════════════════════════╗\n"
            "║     ⚠️ ПОДПИСКА         ║\n"
            "╚══════════════════════════╝\n\n"
            "Для использования бота нужно подписаться на канал!\n\n"
            "Нажми кнопку ниже и вернись обратно.",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        return
    
    # Главное меню
    text = "╔══════════════════════════╗\n"
    text += "║     🚀 NFT ПАРСЕР       ║\n"
    text += "╚══════════════════════════╝\n\n"
    text += f"👋 Привет, @{username}!\n\n"
    text += "🔍 *Быстрый поиск владельцев NFT*\n"
    text += "⚡ Параллельный парсинг (10 запросов/сек)\n"
    text += "🎯 Поиск девушек по никнеймам\n"
    text += "🚫 Бан-лист релеев и ботов\n\n"
    text += f"📊 Всего в базе: {len(NFT_LIST)} NFT"
    
    keyboard = [
        [InlineKeyboardButton("🔍 НАЙТИ ВЛАДЕЛЬЦЕВ", callback_data="search")],
        [InlineKeyboardButton("📢 НАШ КАНАЛ", url=CHANNEL_LINK)]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')

# ========== ОБРАБОТЧИК КНОПОК ==========
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    if data == "search":
        await show_results(update, context, 1)
    elif data.startswith("page_"):
        page = int(data.split("_")[1])
        await show_results(update, context, page)
    elif data == "noop":
        pass

# ========== ЗАПУСК ==========
def main():
    print("╔════════════════════════════════════╗")
    print("║     🚀 NFT ПАРСЕР ЗАПУЩЕН         ║")
    print("╚════════════════════════════════════╝")
    print(f"📢 Канал ID: {CHANNEL_ID}")
    print(f"🔗 Ссылка: {CHANNEL_LINK}")
    print("⚡ Режим: СУПЕР-БЫСТРЫЙ ПАРАЛЛЕЛЬНЫЙ ПАРСИНГ")
    print("🎯 Поиск: владельцы NFT + женские имена")
    print("✅ Кэширование: активное (1 час)")
    print("=" * 40)
    
    app = Application.builder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    
    print("✅ Бот готов к работе!")
    app.run_polling()

if __name__ == "__main__":
    main()
