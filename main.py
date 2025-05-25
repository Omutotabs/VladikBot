import requests
from bs4 import BeautifulSoup
from PIL import Image
import imagehash
import os
import io

# Папка для изображений
os.makedirs("images", exist_ok=True)

# Загрузить ссылки из файла
with open("urls.txt", "r") as f:
    urls = [line.strip() for line in f if line.strip()]

hash_map = {}
report = []

def download_image(url, count):
    try:
        response = requests.get(url, timeout=10)
        img = Image.open(io.BytesIO(response.content)).convert("RGB")
        filename = f"images/img_{count:03}.jpg"
        img.save(filename)
        return img, filename
    except Exception as e:
        print(f"[!] Не удалось загрузить изображение: {url} — {e}")
        return None, None

def get_largest_image_from_page(page_url):
    try:
        res = requests.get(page_url, timeout=10)
        soup = BeautifulSoup(res.text, "html.parser")

        # Сначала ищем og:image
        og_image = soup.find("meta", property="og:image")
        if og_image and og_image.get("content"):
            return og_image["content"]

        imgs = soup.find_all("img")
        max_area = 0
        best_src = None

        for img in imgs:
            src = img.get("src")
            if not src:
                continue
            if src.startswith("//"):
                src = "https:" + src
            elif src.startswith("/"):
                src = requests.compat.urljoin(page_url, src)
            elif not src.startswith("http"):
                continue

            try:
                img_res = requests.get(src, timeout=5)
                im = Image.open(io.BytesIO(img_res.content))
                area = im.size[0] * im.size[1]
                if area > max_area:
                    max_area = area
                    best_src = src
            except:
                continue

        return best_src
    except Exception as e:
        print(f"[!] Ошибка при загрузке страницы {page_url}: {e}")
        return None

count = 0
for page_url in urls:
    img_url = get_largest_image_from_page(page_url)
    if not img_url:
        continue

    img, path = download_image(img_url, count)
    if not img:
        continue

    h = imagehash.phash(img)

    if h in hash_map:
        report.append(f"[Дубликат] {page_url} = {hash_map[h]}")
    else:
        hash_map[h] = page_url

    count += 1

# Сохраняем отчёт
with open("report.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(report) if report else "Дубликаты не найдены.")

print("[✓] Готово. Смотри report.txt")
