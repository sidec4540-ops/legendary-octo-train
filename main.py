import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes

# ========== ТВОИ ДАННЫЕ ==========
BOT_TOKEN = "8430585997:AAFE8C3ostnoTQiwSlwVmYpnVQI5FjbsCRc"
CHANNEL_LINK = "https://t.me/+WLiiYR7_ymZjYWY1"
CHANNEL_ID = -1003256576224

# ========== НАСТРОЙКИ ==========
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

print("🚀 Бот запускается...")
print(f"📢 ID канала: {CHANNEL_ID}")

# ========== ПРОВЕРКА ПОДПИСКИ ==========
async def check_subscription(user_id: int, context: ContextTypes.DEFAULT_TYPE) -> bool:
    try:
        member = await context.bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        return member.status not in ["left", "kicked"]
    except Exception as e:
        print(f"❌ Ошибка проверки: {e}")
        return False

# ========== КОМАНДА START ==========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    username = update.effective_user.username or "друг"
    
    print(f"👉 /start от @{username} ({user_id})")
    
    # Проверяем подписку
    if not await check_subscription(user_id, context):
        print(f"❌ @{username} не подписан")
        keyboard = [[InlineKeyboardButton("📢 Подписаться", url=CHANNEL_LINK)]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            "⚠️ Для использования бота нужно подписаться на канал!\n\nНажми кнопку ниже и вернись обратно.",
            reply_markup=reply_markup
        )
        return
    
    # Если подписан
    print(f"✅ @{username} подписан")
    await update.message.reply_text(
        f"👋 Привет, @{username}!\n\n✅ Спасибо за подписку!\n\nБот работает правильно."
    )

# ========== ЗАПУСК ==========
def main():
    print("✅ Бот готов к работе!")
    print("⏳ Ожидание команд...")
    
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.run_polling()

if __name__ == "__main__":
    main()
