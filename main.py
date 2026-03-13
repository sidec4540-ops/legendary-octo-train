import logging
import random
import re
import time
import requests
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from telegram.constants import ParseMode

# ========== ТВОИ ДАННЫЕ ==========
BOT_TOKEN = "8616937683:AAGSWcZhZWgdBx4y28IhK7Y7kXLab8IrbL0"
CHANNEL_LINK = "https://t.me/+i6Zr8Mk_fYYxMTI0"
CHANNEL_ID = -1003885502543

# ========== БАН-ЛИСТ ==========
BANNED_USERNAMES = {
    "giftrelayer", "mrktbank", "kallent", "monk", "durov",
    "virusgift", "portalsrelayer", "lucha", "snoopdogg", "snoop", 
    "ufc", "nft", "telegram"
}

# ========== ЖЕНСКИЕ ИМЕНА ==========
FEMALE_NAMES = {
    "anna", "anya", "maria", "masha", "olga", "olya", "katya", "kate",
    "nastya", "dasha", "sveta", "lena", "alena", "yana", "vika",
    "анна", "аня", "маша", "катя", "настя", "даша", "света", "лена"
}

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ========== ПРОСТОЙ СПИСОК NFT ==========
NFT_LIST = [
    {"name": "CandyCane", "min_id": 1000, "max_id": 150000},
    {"name": "CloverPin", "min_id": 1000, "max_id": 60000},
    {"name": "CookieHeart", "min_id": 1000, "max_id": 60000},
    {"name": "EasterEgg", "min_id": 1000, "max_id": 60000},
    {"name": "GingerCookie", "min_id": 1000, "max_id": 60000},
    {"name": "HeartLocket", "min_id": 1000, "max_id": 60000},
]

users_db = {}

# ========== ПРОВЕРКА ПОДПИСКИ ==========
async def check_subscription(user_id: int, context: ContextTypes.DEFAULT_TYPE) -> bool:
    try:
        member = await context.bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        return member.status not in ["left", "kicked"]
    except:
        return False

# ========== ПРОСТОЙ ПАРСИНГ ==========
def parse_nft_owner(gift_url: str):
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(gift_url, headers=headers, timeout=3)
        text = response.text
        username_match = re.search(r'@(\w{5,32})', text)
        if username_match:
            return username_match.group(1).lower()
    except:
        pass
    return None

# ========== ПОИСК ==========
async def find_girls(count=5):
    results = []
    used_ids = set()
    
    for _ in range(50):
        nft = random.choice(NFT_LIST)
        nft_id = random.randint(nft["min_id"], nft["max_id"])
        
        if nft_id in used_ids:
            continue
            
        clean_name = re.sub(r"[^\w]", "", nft["name"])
        url = f"https://t.me/nft/{clean_name}-{nft_id}"
        
        username = parse_nft_owner(url)
        
        if username and username not in BANNED_USERNAMES:
            for name in FEMALE_NAMES:
                if name in username:
                    results.append({"username": username, "url": url})
                    break
        
        used_ids.add(nft_id)
        if len(results) >= count:
            break
        time.sleep(0.2)
    
    return results

# ========== START ==========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if not await check_subscription(user_id, context):
        keyboard = [[InlineKeyboardButton("📢 Подписаться", url=CHANNEL_LINK)]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("⚠️ Сначала подпишись на канал!", reply_markup=reply_markup)
        return
    
    keyboard = [[InlineKeyboardButton("🔍 Найти девушек", callback_data="find")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("👋 Привет! Я ищу девушек в NFT-подарках", reply_markup=reply_markup)

# ========== ПОИСК ==========
async def find_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    
    if not await check_subscription(user_id, context):
        keyboard = [[InlineKeyboardButton("📢 Подписаться", url=CHANNEL_LINK)]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.edit_text("⚠️ Сначала подпишись на канал!", reply_markup=reply_markup)
        return
    
    await query.message.edit_text("🔍 Ищу девушек... Подожди немного")
    
    girls = await find_girls(5)
    
    if not girls:
        keyboard = [[InlineKeyboardButton("🔄 Попробовать снова", callback_data="find")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.edit_text("❌ Никого не нашлось. Попробуй еще раз.", reply_markup=reply_markup)
        return
    
    text = "*Найденные девушки:*\n\n"
    for i, girl in enumerate(girls, 1):
        text += f"{i}. @{girl['username']} | [Профиль](tg://user?domain={girl['username']})\n"
    
    keyboard = [[InlineKeyboardButton("🔄 Искать еще", callback_data="find")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.message.edit_text(text, reply_markup=reply_markup, parse_mode='Markdown')

# ========== ЗАПУСК ==========
def main():
    print("🚀 Бот запускается...")
    print(f"📢 ID канала: {CHANNEL_ID}")
    
    app = Application.builder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(find_callback, pattern="^find$"))
    
    print("✅ Бот готов!")
    app.run_polling()

if __name__ == "__main__":
    main()
