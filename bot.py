import logging
import re
import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
import subprocess

TOKEN = "7822028125:AAFLiDfOsV6W2DZ5IK0er8nua9XXAZiv4qs"

# Настройка логов
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# Функция приветствия
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Отправь мне ссылки, и я проверю изображения на дубликаты.")

# Функция обработки сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    # Поиск всех ссылок в тексте (любой формат: пробелы, запятые и т.д.)
    urls = re.findall(r'https?://\S+', text)
    if not urls:
        await update.message.reply_text("Ссылок не найдено. Попробуй ещё раз.")
        return

    # Сохраняем ссылки во временный файл urls.txt
    with open("urls.txt", "w", encoding="utf-8") as f:
        for url in urls:
            f.write(url.strip() + "\n")

    await update.message.reply_text("Обрабатываю... Это может занять до 1–2 минут ⏳")

    # Запускаем main.py
    try:
        subprocess.run(["python", "main.py"], check=True)

        # Читаем результат из report.txt
        with open("report.txt", "r", encoding="utf-8") as f:
            report = f.read()

        await update.message.reply_text(f"Результат:\n\n{report}")
    except Exception as e:
        await update.message.reply_text(f"Произошла ошибка: {e}")

# Основной запуск бота
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))

    print("Бот запущен. Ожидаю сообщения...")
    app.run_polling()

if __name__ == "__main__":
    main()
