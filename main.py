import logging
import random
import re
import json
import time
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

# ========== БАН-ЛИСТ ==========
BANNED_USERNAMES = {
    "giftrelayer", "mrktbank", "kallent", "monk", "durov",
    "virusgift", "portalsrelayer", "lucha", "snoopdogg", "snoop", 
    "ufc", "nft", "telegram", "nftgift", "nftgiftbot", "ton", "gift"
}

# ========== НАСТРОЙКИ ==========
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ========== ПОЛНЫЙ СПИСОК NFT (97 ШТУК) ==========
NFT_LIST = [
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
]

# ========== ХРАНИЛИЩЕ ==========
users_db = {}
user_settings = {}
last_message_ids = {}

# ========== ПАРСИНГ ЮЗЕРНЕЙМА ==========
def parse_nft_username(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=3)
        text = response.text
        username_match = re.search(r'@(\w{5,32})', text)
        if username_match:
            return username_match.group(1).lower()
    except:
        pass
    return None

# ========== ГЕНЕРАЦИЯ ССЫЛОК ==========
def generate_gift_links(nft_name, count=20):
    nft = next((n for n in NFT_LIST if n["name"] == nft_name), None)
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
        available = [n for n in NFT_LIST if n.get("difficulty") == "easy"]
    else:
        available = NFT_LIST
    
    gifts = []
    for _ in range(count):
        nft = random.choice(available)
        clean_name = re.sub(r"[^\w]", "", nft["name"])
        nft_id = random.randint(nft["min_id"], nft["max_id"])
        gifts.append({
            "name": nft["name"],
            "url": f"https://t.me/nft/{clean_name}-{nft_id}"
        })
    return gifts

# ========== ПРОВЕРКА ПОДПИСКИ ==========
async def check_subscription(user_id: int, context) -> bool:
    try:
        member = await context.bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        return member.status not in ["left", "kicked"]
    except:
        return False

# ========== ГЛАВНОЕ МЕНЮ ==========
async def show_main_menu(update: Update, context):
    user = update.effective_user
    text = f"❗ Привет, @{user.username or 'user'}! Это парсер для поиска мамонтов."
    
    keyboard = [
        [InlineKeyboardButton("🔍 Поиск NFT", callback_data="menu_search")],
        [InlineKeyboardButton("👤 Мой профиль", callback_data="menu_profile")],
        [InlineKeyboardButton("📢 Канал", url=CHANNEL_LINK)]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.callback_query:
        await update.callback_query.message.edit_text(text, reply_markup=reply_markup)
    else:
        await update.message.reply_text(text, reply_markup=reply_markup)

# ========== START ==========
async def start(update: Update, context):
    user_id = update.effective_user.id
    
    if not await check_subscription(user_id, context):
        keyboard = [[InlineKeyboardButton("📢 Подписаться", url=CHANNEL_LINK)]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("⚠️ Подпишись на канал!", reply_markup=reply_markup)
        return
    
    await show_main_menu(update, context)

# ========== МЕНЮ ПОИСКА ==========
async def show_search_menu(update: Update, context):
    query = update.callback_query
    text = "Выберите тип поиска:"
    keyboard = [
        [InlineKeyboardButton("🎲 Рандом поиск", callback_data="search_random")],
        [InlineKeyboardButton("👧 Поиск девушек", callback_data="search_girls")],
        [InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.message.edit_text(text, reply_markup=reply_markup)

# ========== ПОКАЗ РЕЗУЛЬТАТОВ ==========
async def show_search_results(update: Update, context, mode, nft_name=None, page=1):
    query = update.callback_query
    count = 20
    
    if nft_name:
        links = generate_gift_links(nft_name, count)
        gifts = [{"name": nft_name, "url": url} for url in links]
    elif mode == "girls":
        gifts = generate_random_gifts("light", count)
    else:
        gifts = generate_random_gifts(mode, count)
    
    # Добавляем юзернеймы
    results = []
    for gift in gifts:
        username = parse_nft_username(gift["url"])
        if username and username not in BANNED_USERNAMES:
            results.append({
                "name": gift["name"],
                "url": gift["url"],
                "username": username
            })
            if len(results) >= 5:
                break
    
    if not results:
        await query.message.edit_text("❌ Ничего не найдено")
        return
    
    text = "*Результаты поиска*\n\n"
    for i, r in enumerate(results, 1):
        text += f"{i}. 👤 @{r['username']}\n   🎁 [{r['name']}]({r['url']})\n\n"
    
    keyboard = [
        [InlineKeyboardButton("🔄 Новый поиск", callback_data="search_random")],
        [InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.message.edit_text(text, reply_markup=reply_markup, parse_mode='Markdown', disable_web_page_preview=True)

# ========== ПРОФИЛЬ ==========
async def show_profile(update: Update, context):
    query = update.callback_query
    user_id = query.from_user.id
    user = users_db.get(user_id, {})
    text = f"ID: {user_id}\nUsername: @{user.get('username', 'unknown')}"
    keyboard = [[InlineKeyboardButton("◀️ Назад", callback_data="main_menu")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.message.edit_text(text, reply_markup=reply_markup)

# ========== ОБРАБОТЧИК ==========
async def handle_menu(update: Update, context):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    if not await check_subscription(user_id, context):
        keyboard = [[InlineKeyboardButton("📢 Подписаться", url=CHANNEL_LINK)]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.edit_text("⚠️ Подпишись на канал!", reply_markup=reply_markup)
        return
    
    data = query.data
    
    if data == "main_menu":
        await show_main_menu(update, context)
    elif data == "menu_search":
        await show_search_menu(update, context)
    elif data == "menu_profile":
        await show_profile(update, context)
    elif data == "search_random":
        await show_search_results(update, context, "light")
    elif data == "search_girls":
        await show_search_results(update, context, "girls")

# ========== ЗАПУСК ==========
def main():
    print("🚀 Бот запущен")
    app = Application.builder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_menu))
    
    print("✅ Бот готов")
    app.run_polling()

if __name__ == "__main__":
    main()