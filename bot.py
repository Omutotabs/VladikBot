import logging
import re
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from PIL import Image
import requests
import imagehash
from io import BytesIO
from bs4 import BeautifulSoup
import os

TOKEN = "7822028125:AAFLiDfOsV6W2DZ5IK0er8nua9XXAZiv4qs"

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

IMAGE_DIR = "images"
os.makedirs(IMAGE_DIR, exist_ok=True)

# Удаление всех файлов из папки с картинками
def clear_dir():
    for f in os.listdir(IMAGE_DIR):
        try:
            os.remove(os.path.join(IMAGE_DIR, f))
        except Exception:
            pass

# Скачивание изображения по ссылке (ищет первую картинку на странице)
def fetch_image_from_url(url, idx):
    try:
        res = requests.get(url, timeout=10)
        soup = BeautifulSoup(res.text, "html.parser")
        img_tag = soup.find("img")
        if img_tag and "src" in img_tag.attrs:
            img_url = img_tag["src"]
            if not img_url.startswith("http"):
                img_url = "https:" + img_url
            img_data = requests.get(img_url, timeout=10).content
            filename = os.path.join(IMAGE_DIR, f"url_{idx}.jpg")
            with open(filename, "wb") as f:
                f.write(img_data)
            return filename
    except Exception:
        pass
    return None

# Скачивание изображения из Telegram
async def fetch_image_from_telegram(photo, idx, context):
    file = await context.bot.get_file(photo.file_id)
    img_data = await file.download_as_bytearray()
    filename = os.path.join(IMAGE_DIR, f"tg_{idx}.jpg")
    with open(filename, "wb") as f:
        f.write(img_data)
    return filename

# Вычисление хэша
def compute_hash(image_path):
    try:
        img = Image.open(image_path)
        return imagehash.phash(img)
    except Exception:
        return None

# Поиск дубликатов
def find_duplicates(image_paths):
    hashes = {}
    duplicates = []
    for idx, path in enumerate(image_paths):
        h = compute_hash(path)
        if h is None:
            continue
        for other_idx, (other_path, other_h) in enumerate(hashes.items()):
            if abs(h - other_h) <= 8:  # Меньше = строже
                duplicates.append((idx + 1, other_idx + 1))
        hashes[path] = h
    return duplicates

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Пришли мне **ссылки на сайты с фото** или **отправь несколько фото** одним сообщением — я найду дубликаты!")

async def handle_all(update: Update, context: ContextTypes.DEFAULT_TYPE):
    clear_dir()
    # Если ссылки в тексте
    image_paths = []
    if update.message.text:
        urls = re.findall(r'https?://\S+', update.message.text)
        for i, url in enumerate(urls):
            path = fetch_image_from_url(url, i)
            if path:
                image_paths.append(path)
    # Если фото
    if update.message.photo:
        # Получить все фото, если это альбом
        photo_sizes = update.message.photo
        if photo_sizes:
            for i, photo in enumerate(photo_sizes):
                path = await fetch_image_from_telegram(photo, i, context)
                image_paths.append(path)

    if len(image_paths) < 2:
        await update.message.reply_text("Отправь хотя бы **2 фото** или **2 ссылки**!")
        clear_dir()
        return

    duplicates = find_duplicates(image_paths)
    if duplicates:
        lines = [f"Фото №{a} == Фото №{b}" for a, b in duplicates]
        await update.message.reply_text("Найдены дубликаты:\n" + "\n".join(lines))
    else:
        await update.message.reply_text("Дубликаты не найдены.")
    clear_dir()

def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.ALL, handle_all))
    app.run_polling()

if __name__ == "__main__":
    main()
