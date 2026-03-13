import logging
import random
import re
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
    "virusgift", "portalsrelayer", "lucha", "snoopdogg", "ufc"
}

# ========== КЭШ ==========
parser_cache = {}

# ========== NFT (ТОЛЬКО РАБОЧИЕ) ==========
NFT_LIST = [
    {"name": "CandyCane", "min_id": 1000, "max_id": 150000},
    {"name": "CloverPin", "min_id": 1000, "max_id": 60000},
    {"name": "CookieHeart", "min_id": 1000, "max_id": 60000},
    {"name": "GingerCookie", "min_id": 1000, "max_id": 60000},
    {"name": "HeartLocket", "min_id": 1000, "max_id": 60000},
]

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ========== ПРОВЕРКА ПОДПИСКИ ==========
async def check_subscription(user_id: int, context) -> bool:
    try:
        member = await context.bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        return member.status not in ["left", "kicked"]
    except:
        return False

# ========== СУПЕР-БЫСТРЫЙ ПАРСИНГ ==========
async def fast_parse(session, url):
    if url in parser_cache:
        return parser_cache[url]
    
    try:
        async with session.get(url, timeout=2) as resp:
            if resp.status != 200:
                return None
            text = await resp.text()
            match = re.search(r'@(\w{5,32})', text)
            if match:
                username = match.group(1).lower()
                if username not in BANNED_USERNAMES:
                    parser_cache[url] = username
                    return username
    except:
        pass
    parser_cache[url] = None
    return None

# ========== БЫСТРЫЙ ПОИСК (5 ЗАПРОСОВ РАЗОМ) ==========
async def quick_search(count=5):
    async with aiohttp.ClientSession() as session:
        tasks = []
        urls = []
        used_ids = set()
        
        # Генерим URL
        for _ in range(count * 3):
            nft = random.choice(NFT_LIST)
            nft_id = random.randint(nft["min_id"], nft["max_id"])
            if nft_id in used_ids:
                continue
            used_ids.add(nft_id)
            clean_name = re.sub(r"[^\w]", "", nft["name"])
            urls.append(f"https://t.me/nft/{clean_name}-{nft_id}")
        
        # Долбим параллельно
        tasks = [fast_parse(session, url) for url in urls]
        results = await asyncio.gather(*tasks)
        
        # Собираем только успешные
        found = []
        for url, username in zip(urls, results):
            if username and len(found) < count:
                found.append({"url": url, "username": username})
        return found

# ========== СТАРТ ==========
async def start(update: Update, context):
    user_id = update.effective_user.id
    if not await check_subscription(user_id, context):
        keyboard = [[InlineKeyboardButton("📢 Подписаться", url=CHANNEL_LINK)]]
        await update.message.reply_text("⚠️ Подпишись на канал!", reply_markup=InlineKeyboardMarkup(keyboard))
        return
    
    keyboard = [[InlineKeyboardButton("🔍 БЫСТРЫЙ ПОИСК", callback_data="search")]]
    await update.message.reply_text("🚀 Бот для поиска владельцев NFT", reply_markup=InlineKeyboardMarkup(keyboard))

# ========== ПОИСК ==========
async def search(update: Update, context):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    if not await check_subscription(user_id, context):
        keyboard = [[InlineKeyboardButton("📢 Подписаться", url=CHANNEL_LINK)]]
        await query.message.edit_text("⚠️ Подпишись на канал!", reply_markup=InlineKeyboardMarkup(keyboard))
        return
    
    await query.message.edit_text("⏳ Секунду...")
    
    results = await quick_search(5)
    
    if not results:
        await query.message.edit_text("❌ Никого нет", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔄 Еще", callback_data="search")]]))
        return
    
    text = "*Найденные владельцы:*\n\n"
    for i, r in enumerate(results, 1):
        text += f"{i}. 👤 @{r['username']}\n   🔗 [Ссылка]({r['url']})\n\n"
    
    keyboard = [[InlineKeyboardButton("🔄 ЕЩЕ", callback_data="search")]]
    await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown', disable_web_page_preview=True)

# ========== ЗАПУСК ==========
def main():
    print("🚀 ЗАПУСК БЫСТРОГО БОТА")
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(search, pattern="^search$"))
    print("✅ ГОТОВО")
    app.run_polling()

if __name__ == "__main__":
    main()