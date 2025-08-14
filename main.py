import logging
import asyncio
import random
from datetime import datetime, timedelta
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    ConversationHandler, ContextTypes, filters
)

# Состояния для ConversationHandler
USERNAME, CHOICE, QR, CODE, SUCCESS = range(5)

WELCOME_TEXT = (
    'Вас приветствует бот "Roblox вход в аккаунты"! Введите имя пользователя, и мы для вас найдём этот аккаунт!'
)
CHOICE_KEYBOARD = [['Почта', 'QR-код', 'Код', 'Пароль']]

BROKEN_TEXT = (
    "ĦŶŶéŔģţĪĪīşĦŁ╜п↑ХĂĂ¢¤¥¥1>cz¢G11yÝõõÞ§J$$$AX444=°Ê¥¥´ÚÆD0Dk´k///rêćĈĮЛ₧ХΏΤк≥○┌ỳь“⅝‾₣⌡◘◘♀―ŔÜ©×¶·ÙŉΜΣţǻǻΛĬkkÈΕΕćġĲġñĈŻŻĭðĐśŞįĉĈŀŘřřŻĴº!!¶żс█♂◊ﬁﬁ♥♪♪♪♪♪♪♪♫♫♂▓▓♪♪♪♪в™♪♪┤в™♪╠ћц∞♪♪♪♪♪∆'..."
)
BLUE_SCREEN_TEXT = (
    "A problem has been detected and windows has been shut down to prevent damage to your computer.\n\n"
    "If this is the first time you've seen this stop error screen, restart your computer. If this screen appears again, follow these steps:\n\n"
    "Check to be sure you have adequate disk space. If a driver is identified in the stop message, disable the driver or check with the manufacturer for driver updates. Try changing video adapters.\n"
    "Check with your hardware vendor for any BIOS updates. Disable BIOS memory options such as caching or shadowing. If you need to use Safe Mode to remove or disable components, restart your computer, press F8 to select Advanced Startup options, and then select safe Mode.\n\n"
    "Technical information:\n\n"
    "STOP: 0x0000007E (0xC0000005, 0xF74860BF, 0xF780A208, 0xF7809F08)\n"
    "pc1.sys Address F74860BF base at F7487000, DateStamp"
)

UPDATE_MESSAGES = [
    "Бот закрылся на обновление",
    "Идёт обновление...",
    "⬜⬜⬜⬜⬜⬜",
    "🟩⬜⬜⬜⬜⬜",
    "🟩🟩⬜⬜⬜⬜",
    "🟩🟩🟩⬜⬜⬜",
    "🟩🟩🟩🟩⬜⬜",
    "🟩🟩🟩🟩🟩⬜",
    "🟩🟩🟩🟩🟩🟩",
    "Обновление завершено✅"
]
UPDATE_TIME_SECONDS = 180  # 3 минуты = 180 секунд
UPDATE_STEPS = len(UPDATE_MESSAGES)
UPDATE_INTERVAL = UPDATE_TIME_SECONDS // (UPDATE_STEPS - 2)  # первые два — сразу, остальное с равным интервалом

RECOVERY_MESSAGES = [
    "Подготовка автоматического восстановления.",
    "🟩⬜⬜⬜⬜⬜",
    "🟩🟩⬜⬜⬜⬜",
    "🟩🟩🟩⬜⬜⬜",
    "🟩🟩🟩🟩⬜⬜",
    "🟩🟩🟩🟩🟩⬜",
    "🟩🟩🟩🟩🟩🟩"
]
RECOVERY_TIME_SECONDS = 60  # 1 минута = 60 секунд
RECOVERY_INTERVAL = RECOVERY_TIME_SECONDS // (len(RECOVERY_MESSAGES) - 1)

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

user_last_seen = {}
user_update_count = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    now = datetime.utcnow()
    last_seen = user_last_seen.get(user_id)
    force_update = False

    if random.random() < 0.10:
        force_update = True

    if last_seen is None or (now - last_seen > timedelta(days=3)) or force_update:
        user_update_count[user_id] = user_update_count.get(user_id, 0) + 1
        await fake_update(update)
        user_last_seen[user_id] = now
    else:
        user_last_seen[user_id] = now

    await update.message.reply_text(WELCOME_TEXT)
    return USERNAME

async def fake_update(update: Update):
    await update.message.reply_text(UPDATE_MESSAGES[0])
    await asyncio.sleep(1)
    await update.message.reply_text(UPDATE_MESSAGES[1])
    await asyncio.sleep(1)
    for msg in UPDATE_MESSAGES[2:-1]:
        await update.message.reply_text(msg)
        await asyncio.sleep(UPDATE_INTERVAL)
    await update.message.reply_text(UPDATE_MESSAGES[-1])

async def fake_recovery(update: Update):
    for msg in RECOVERY_MESSAGES:
        await update.message.reply_text(msg)
        await asyncio.sleep(RECOVERY_INTERVAL)
    await update.message.reply_text("Восстановление завершено. Бот снова готов к работе!")

async def get_username(update: Update, context: ContextTypes.DEFAULT_TYPE):
    username = update.message.text
    context.user_data['username'] = username
    await update.message.reply_text(
        f'Аккаунт "{username}" найден или создан.\n'
        'Выберите способ входа:',
        reply_markup=ReplyKeyboardMarkup(CHOICE_KEYBOARD, one_time_keyboard=True)
    )
    return CHOICE

async def choose_method(update: Update, context: ContextTypes.DEFAULT_TYPE):
    choice = update.message.text.lower()
    context.user_data['choice'] = choice
    if choice == 'почта':
        await update.message.reply_text('Создаю временную почту...')
        temp_email = 'example@tempmail.com'
        context.user_data['email'] = temp_email
        await update.message.reply_text(f"Почта для входа: {temp_email}")
        return SUCCESS
    elif choice == 'qr-код':
        await update.message.reply_text('Пожалуйста, отправьте скриншот страницы входа с QR-кодом.')
        return QR
    elif choice == 'код':
        await update.message.reply_text('Пожалуйста, отправьте скриншот с кодом входа.')
        return CODE
    elif choice == 'пароль':
        password = 'P@ssw0rd123'
        context.user_data['password'] = password
        await update.message.reply_text(
            f"Логин: {context.user_data['username']}\nПароль: {password}"
        )
        return SUCCESS
    else:
        await update.message.reply_text('Пожалуйста, выберите один из предложенных вариантов.')
        return CHOICE

async def handle_qr(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Вход выполнен, спасибо за выбор.')
    return SUCCESS

async def handle_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Вход выполнен, спасибо за выбор.')
    return SUCCESS

async def success(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Вход выполнен, спасибо за выбор.')
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Процесс прерван.')
    return ConversationHandler.END

async def broken_mode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    for i in range(60):
        await update.message.reply_text(BROKEN_TEXT)
        await asyncio.sleep(5)
    await update.message.reply_text(BLUE_SCREEN_TEXT)
    # После "поломки" запускаем восстановление
    await fake_recovery(update)
    await update.message.reply_text(WELCOME_TEXT)

async def update_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    count = user_update_count.get(user_id, 0)
    await update.message.reply_text(f"Фейковое обновление запускалось для вас {count} раз(а).")

def main():
    application = ApplicationBuilder().token('8013431816:AAFpfkZnd4kTCWv33mkfS5JYW7Yp1Fo-r2c').build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            USERNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_username)],
            CHOICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, choose_method)],
            QR: [MessageHandler(filters.PHOTO, handle_qr)],
            CODE: [MessageHandler(filters.PHOTO, handle_code)],
            SUCCESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, success)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    application.add_handler(conv_handler)
    application.add_handler(CommandHandler("e_gswinniteosm", broken_mode))
    application.add_handler(CommandHandler("update_stats", update_stats))

    application.run_polling()

if __name__ == '__main__':
    main()

    # ---- Добавлено для запуска Flask-сервера ----
    from flask import Flask
    from threading import Thread

    app = Flask('')

    @app.route('/')
    def home():
        return "Bot is alive!"

    def run():
        app.run(host='0.0.0.0', port=8080)

    def keep_alive():
        t = Thread(target=run)
        t.start()

    # Запускаем веб-сервер
    keep_alive()
