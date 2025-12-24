import httpx
import asyncio
from collections import deque
import feedparser
import csv
import os

async def rss_parser(httpx_client, posted_q, n_test_chars, csv_path='data/rbc.csv', maxnews = 4000):
    """Парсер RSS-ленты РБК с записью в CSV"""

    rss_link = 'https://rssexport.rbc.ru/rbcnews/news/30/full.rss'

    # Создаём файл, если его нет
    if not os.path.exists(csv_path):
        open(csv_path, 'w', encoding='utf-8').close()

    count = 0
    while count < maxnews:
        try:
            response = await httpx_client.get(rss_link, timeout=10)
            response.raise_for_status()
        except httpx.RequestError as e:
            print(f"Ошибка запроса: {e}")
            await asyncio.sleep(10)
            continue
        except httpx.HTTPStatusError as e:
            print(f"Ошибка статуса: {e}")
            await asyncio.sleep(10)
            continue

        feed = feedparser.parse(response.text)

        for entry in feed.entries[::-1]:
            summary = entry.get('summary', '')
            title = entry.get('title', '')

            news_text = f'{title}\n{summary}'
            head = news_text[:n_test_chars].strip()

            # Проверка на дубликаты
            if head in posted_q:
                continue

            # Записываем новость в CSV (одна строка, один столбец)
            with open(csv_path, 'a', encoding='utf-8', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([news_text])
                count += 1

            posted_q.appendleft(head)

        await asyncio.sleep(1)  # проверяем каждые 1 секунд

async def main():
    posted_q = deque(maxlen=20)
    n_test_chars = 50

    async with httpx.AsyncClient() as httpx_client:
        await rss_parser(httpx_client, posted_q, n_test_chars, 'data/rbc.csv', 500)

if __name__ == "__main__":
    os.makedirs("data", exist_ok=True)
    asyncio.run(main())
