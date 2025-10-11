import requests
from bs4 import BeautifulSoup
import time
import os

FORUM_URL = "https://forum.gta5rp.com/forums/verxovnyi-sud.1834/"
WEBHOOK_URL = "https://discord.com/api/webhooks/1424215766445719652/XJmp_Y7f6KTNJ41eKxaQAD0z0KJax4jhl2-SdIrtssoBqRdL6Ty4olwF_VAZGXhR0Ten"
TOPIC_SELECTOR = "div.structItem-title > a:not(.labelLink)"
CHECK_INTERVAL = 60
SEEN_FILE = "supremecourt_links.txt"

def get_all_links():
    """Возвращает список кортежей (ссылка, название темы)"""
    response = requests.get(FORUM_URL, timeout=10)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    topics = soup.select(TOPIC_SELECTOR)
    return [(topic.get("href"), topic.text.strip()) for topic in topics if topic.get("href")]

# --- ПЕРВЫЙ ЗАПУСК ---
if not os.path.exists(SEEN_FILE):
    print("⏳ Первый запуск: собираем все текущие темы (не отправляем)")
    links = get_all_links()
    seen_links = set()
    for href, _ in links:
        if not href.startswith("http"):
            href = requests.compat.urljoin(FORUM_URL, href)
        seen_links.add(href)
    with open(SEEN_FILE, "w") as f:
        for href in seen_links:
            f.write(href + "\n")
    print("✅ Старые темы сохранены, уведомлений не отправлено.")
else:
    with open(SEEN_FILE, "r") as f:
        seen_links = set(line.strip() for line in f)

print("✅ Скрипт запущен. Отслеживаю только новые темы...")

# --- ОСНОВНОЙ ЦИКЛ ---
while True:
    try:
        links = get_all_links()
        for href, title in links:
            if not href.startswith("http"):
                href = requests.compat.urljoin(FORUM_URL, href)
            if href not in seen_links:
                # Новая тема — отправляем
                data = {"content": f"🆕 Новая тема: **{title}**\n🔗 {href}"}
                requests.post(WEBHOOK_URL, json=data)
                print(f"📨 Отправлено: {title}")

                # Добавляем в список и файл
                seen_links.add(href)
                with open(SEEN_FILE, "a") as f:
                    f.write(href + "\n")

        time.sleep(CHECK_INTERVAL)

    except Exception as e:
        print(f"⚠️ Ошибка: {e}")
        time.sleep(CHECK_INTERVAL)