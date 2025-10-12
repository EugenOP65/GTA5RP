from datetime import datetime

def format_russian_datetime(dt_str):
    # Исправляем +0300 на +03:00
    if len(dt_str) > 5 and (dt_str[-5] == '+' or dt_str[-5] == '-') and dt_str[-2] != ':':
        dt_str = dt_str[:-2] + ':' + dt_str[-2:]
    dt = datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
    months = [
        '', 'января', 'февраля', 'марта', 'апреля', 'мая', 'июня',
        'июля', 'августа', 'сентября', 'октября', 'ноября', 'декабря'
    ]
    return f"{dt.day} {months[dt.month]} в {dt.strftime('%H:%M')}"
import requests
from bs4 import BeautifulSoup
import time
import os

FORUM_URLS = {
    "Верховный суд": "https://forum.gta5rp.com/forums/verxovnyi-sud.1834/",
    "Окружной суд": "https://forum.gta5rp.com/forums/okruzhnoi-sud.1835/",
    "УДО и Реабилитация осуждённых": "https://forum.gta5rp.com/forums/udo-i-reabilitacija-osuzhdennyx.1838/",
}
WEBHOOK_URL = "https://discord.com/api/webhooks/1424215766445719652/XJmp_Y7f6KTNJ41eKxaQAD0z0KJax4jhl2-SdIrtssoBqRdL6Ty4olwF_VAZGXhR0Ten"
TOPIC_SELECTOR = "div.structItem-title > a:not(.labelLink)"
NAME_SELECTOR = "ul.structItem-parts > li:not(.structItem-startDate) > a"
TIME_SELECTOR = "li.structItem-startDate > a > time"
CHECK_INTERVAL = 60
SEEN_FILE = "supremecourt_links.txt"
webhook_url = "https://discord.com/api/webhooks/1424215766445719652/XJmp_Y7f6KTNJ41eKxaQAD0z0KJax4jhl2-SdIrtssoBqRdL6Ty4olwF_VAZGXhR0Ten"

def get_all_forum_urls():
    """Возвращает список всех URL форумов"""
    return list(FORUM_URLS.values())

def get_all_links():
    """Возвращает список кортежей (ссылка, название темы, форум, автор, время)"""
    results = []
    for forum_title, url in FORUM_URLS.items():
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        topics = soup.select(TOPIC_SELECTOR)
        authors = soup.select(NAME_SELECTOR)
        times = soup.select(TIME_SELECTOR)
        for topic, author, timestamp in zip(topics, authors, times):
            href = topic.get("href")
            if href:
                results.append((href, topic.text.strip(), forum_title, author.text.strip(), timestamp.get("datetime", str(timestamp))))
    return results

def send_to_discord(forum_title, tag_list, topic_title, author, timestamp, link):
    """Отправляет сообщение в Discord через вебхук"""
    formatted_time = format_russian_datetime(timestamp)
    data = {
        
        "content": ", ".join(tag_list),
        "embeds": [
            {
                "title": f"{forum_title}: {topic_title}",
                "description": link,
                "color": int("2f3136", 16),
                "fields": [
                    {
                        "name": "Подано",
                        "value": formatted_time,
                        "inline": False
                    },
                    {
                        "name": "Автор",
                        "value": str(author),
                        "inline": False
                    }
                ],
                "footer": {
                    "text": "🧿 Created by Eugen Norman | Discord for communication - eugen_op."
                }
            }
        ]
    }
    response = requests.post(WEBHOOK_URL, json=data)
    time.sleep(1)
    response.raise_for_status()

# --- ПЕРВЫЙ ЗАПУСК ---
if not os.path.exists(SEEN_FILE):
    print("⏳ Первый запуск: собираем все текущие темы (не отправляем)")
    links = get_all_links()
    seen_links = set()
    for href, _ in links:
        for forum_url in get_all_forum_urls():
            if not href.startswith("http"):
                href = requests.compat.urljoin(forum_url, href)
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
        for href, title, forum_title, author, timestamp in links:
            match forum_title:
                case "Верховный суд":
                    tag_list = ["<@&1332717305154637896> <@&1316096152113905665>"]
                case "Окружной суд":
                    tag_list = ["<@&1316096160443666504>"]
                case "УДО и Реабилитация осуждённых":
                    tag_list = ["<@&1316096152113905665> <@&1316096203385213001>"]
            for forum_url in get_all_forum_urls():
                if not href.startswith("http"):
                    href = requests.compat.urljoin(forum_url, href)
            if href not in seen_links:
                # Новая тема — отправляем в Discord
                send_to_discord(forum_title, tag_list, title, author, timestamp, href)
                print(f"📨 {forum_title}: {title}")

                # Добавляем в список и файл
                seen_links.add(href)
                with open(SEEN_FILE, "a") as f:
                    f.write(href + "\n")

        time.sleep(CHECK_INTERVAL)

    except Exception as e:
        print(f"⚠️ Ошибка: {e}")
        time.sleep(CHECK_INTERVAL)