import logging
import random
import re
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
    "ufc", "nft", "telegram", "nftgift", "nftgiftbot", "ton", "gift"
}

# ========== НАСТРОЙКИ ==========
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ========== ТВОЙ СПИСОК NFT (97 ШТУК) ==========
NFT_LIST = [
    {"name": "AstralShard", "slug": "astralshard", "min_id": 1, "max_id": 1550},
    {"name": "BDayCandle", "slug": "bdaycandle", "min_id": 1, "max_id": 20000},
    {"name": "BerryBox", "slug": "berrybox", "min_id": 1, "max_id": 60000},
    {"name": "BigYear", "slug": "bigyear", "min_id": 1, "max_id": 60000},
    {"name": "BowTie", "slug": "bowtie", "min_id": 1, "max_id": 47000},
    {"name": "BunnyMuffin", "slug": "bunnymuffin", "min_id": 1, "max_id": 60000},
    {"name": "CandyCane", "slug": "candycane", "min_id": 1, "max_id": 150000},
    {"name": "CloverPin", "slug": "cloverpin", "min_id": 1, "max_id": 60000},
    {"name": "CookieHeart", "slug": "cookieheart", "min_id": 1, "max_id": 60000},
    {"name": "DeskCalendar", "slug": "deskcalender", "min_id": 1, "max_id": 13000},
    {"name": "DiamondRing", "slug": "diamondring", "min_id": 1, "max_id": 60000},
    {"name": "EasterEgg", "slug": "easteregg", "min_id": 1, "max_id": 60000},
    {"name": "EternalRose", "slug": "eternalrose", "min_id": 1, "max_id": 60000},
    {"name": "FaithAmulet", "slug": "faithamulet", "min_id": 1, "max_id": 60000},
    {"name": "FreshSocks", "slug": "freshsocks", "min_id": 1, "max_id": 100000},
    {"name": "GingerCookie", "slug": "gingercookie", "min_id": 1, "max_id": 60000},
    {"name": "HappyBrownie", "slug": "happybrownie", "min_id": 1, "max_id": 60000},
    {"name": "HeartLocket", "slug": "heartlocket", "min_id": 1, "max_id": 60000},
    {"name": "HolidayDrink", "slug": "holidaydrink", "min_id": 1, "max_id": 60000},
    {"name": "HomemadeCake", "slug": "homemadecake", "min_id": 1, "max_id": 130000},
    {"name": "IceCream", "slug": "icecream", "min_id": 1, "max_id": 60000},
    {"name": "InstantRamen", "slug": "instantramen", "min_id": 1, "max_id": 60000},
    {"name": "JackInTheBox", "slug": "jackinthebox", "min_id": 1, "max_id": 60000},
    {"name": "JesterHat", "slug": "jesterhat", "min_id": 1, "max_id": 60000},
    {"name": "JingleBells", "slug": "jinglebells", "min_id": 1, "max_id": 60000},
    {"name": "LolPop", "slug": "lolpop", "min_id": 1, "max_id": 130000},
    {"name": "LoveCandle", "slug": "lovecandle", "min_id": 1, "max_id": 60000},
    {"name": "LovePotion", "slug": "lovepotion", "min_id": 1, "max_id": 60000},
    {"name": "LunarSnake", "slug": "lunarsnake", "min_id": 1, "max_id": 250000},
    {"name": "PetSnake", "slug": "petsnake", "min_id": 1, "max_id": 1000},
    {"name": "Rose", "slug": "rose", "min_id": 1, "max_id": 60000},
    {"name": "SnakeBox", "slug": "snakebox", "min_id": 1, "max_id": 55000},
    {"name": "SnoopDogg", "slug": "snoopdogg", "min_id": 576241, "max_id": 576241},
    {"name": "SpicedWine", "slug": "spicedwine", "min_id": 93557, "max_id": 93557},
    {"name": "WhipCupcake", "slug": "whipcupcake", "min_id": 1, "max_id": 170000},
    {"name": "WinterWreath", "slug": "winterwreath", "min_id": 65311, "max_id": 65311},
    {"name": "XmasStocking", "slug": "xmasstocking", "min_id": 177478, "max_id": 177478},
]

# ========== ХРАНИЛИЩЕ ==========
users_db = {}

# ========== ПРОВЕРКА ПОДПИСКИ ==========
async def check_subscription(user_id: int, context) -> bool:
    try:
        member = await context.bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        return member.status not in ["left", "kicked"]
    except:
        return False

# ========== ПАРСЕР (БЕЗ ЛИШНИХ ЛОГОВ) ==========
async def fetch_gift_info(session, gift_name, gift_number):
    url = f"https://t.me/nft/{gift_name}-{gift_number}"
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    try:
        async with session.get(url, headers=headers, timeout=10) as resp:
            if resp.status != 200:
                return None
            text = await resp.text()
            
            # Ищем JSON в data-атрибутах или скриптах
            data_match = re.search(r'<script[^>]*>.*?window\.initData\s*=\s*({.*?});', text, re.DOTALL)
            if data_match:
                try:
                    data = json.loads(data_match.group(1))
                    if 'owner' in data:
                        owner = data['owner']
                        if owner.get('type') == 'entity' and 'username' in owner:
                            username = owner['username'].lower()
                            if username not in BANNED_USERNAMES:
                                return {'username': username, 'url': url, 'name': gift_name}
                except:
                    pass
            
            # Ищем обычный username
            username_match = re.search(r'@(\w{5,32})', text)
            if username_match:
                username = username_match.group(1).lower()
                if username not in BANNED_USERNAMES:
                    return {'username': username, 'url': url, 'name': gift_name}
            
            return None
    except:
        return None

# ========== ПОИСК ==========
async def find_gifts(count=5):
    async with aiohttp.ClientSession() as session:
        tasks = []
        params = []
        used_ids = set()
        
        for _ in range(count * 5):
            nft = random.choice(NFT_LIST)
            nft_id = random.randint(nft["min_id"], nft["max_id"])
            if nft_id in used_ids:
                continue
            used_ids.add(nft_id)
            params.append((nft["slug"], nft_id, nft["name"]))
        
        results = await asyncio.gather(*[
            fetch_gift_info(session, slug, nft_id) for slug, nft_id, _ in params
        ])
        
        found = []
        for res in results:
            if res and len(found) < count:
                found.append(res)
        return found

# ========== START ==========
async def start(update: Update, context):
    user_id = update.effective_user.id
    if not await check_subscription(user_id, context):
        keyboard = [[InlineKeyboardButton("📢 Подписаться", url=CHANNEL_LINK)]]
        await update.message.reply_text("⚠️ Подпишись на канал!", reply_markup=InlineKeyboardMarkup(keyboard))
        return
    await update.message.reply_text("👋 Привет! Жми кнопку поиска 👇", 
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔍 ПОИСК", callback_data="search")]]))

# ========== ПОИСК ==========
async def search_callback(update: Update, context):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    if not await check_subscription(user_id, context):
        keyboard = [[InlineKeyboardButton("📢 Подписаться", url=CHANNEL_LINK)]]
        await query.message.edit_text("⚠️ Подпишись на канал!", reply_markup=InlineKeyboardMarkup(keyboard))
        return
    
    await query.message.edit_text("🔍 Ищу...")
    results = await find_gifts(5)
    
    if not results:
        await query.message.edit_text("❌ Ничего нет. Попробуй ещё.", 
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔄 ЕЩЁ", callback_data="search")]]))
        return
    
    text = "*Найдено:*\n\n"
    for i, r in enumerate(results, 1):
        text += f"{i}. 👤 @{r['username']}\n   🎁 [Ссылка]({r['url']})\n\n"
    
    keyboard = [
        [InlineKeyboardButton("🔄 ЕЩЁ", callback_data="search")],
        [InlineKeyboardButton("🏠 МЕНЮ", callback_data="menu")]
    ]
    await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown', disable_web_page_preview=True)

# ========== МЕНЮ ==========
async def menu_callback(update: Update, context):
    query = update.callback_query
    await query.answer()
    await query.message.edit_text("👋 Жми кнопку поиска 👇", 
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔍 ПОИСК", callback_data="search")]]))

# ========== ЗАПУСК ==========
def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(search_callback, pattern="^search$"))
    app.add_handler(CallbackQueryHandler(menu_callback, pattern="^menu$"))
    print("✅ Бот готов")
    app.run_polling()

if __name__ == "__main__":
    main()