# Твой текст
text = "❗ Привет, @{user.username or 'user'}! Это парсер для поиска мамонтов."

# Кнопки
keyboard = [ ... ] 

# Вместо старого bot.send_message вставь это:
if update.callback_query:
    await update.callback_query.message.reply_photo(
        photo="https://i.imgur.com/I1rr27s.jpg",  # 👈 Ссылка на баннер "Меню"
        caption=text,
        reply_markup=reply_markup
    )
else:
    await update.message.reply_photo(
        photo="https://i.imgur.com/I1rr27s.jpg",  # 👈 Ссылка на баннер "Меню"
        caption=text,
        reply_markup=reply_markup
    )