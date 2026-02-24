#!/usr/bin/env python3
"""
Парсер новостей с Известия / iz.ru (RSS).
Сохраняет тексты в CSV без заголовков.
"""

import httpx
import asyncio
from collections import deque
import feedparser
import csv
import os


async def rss_parser(httpx_client, posted_q, n_test_chars, csv_path='data/izvestia.csv', maxnews=4000):
    """Парсер RSS-ленты Известий с записью в CSV"""

    rss_link = 'https://iz.ru/xml/rss/all.xml'

    if not os.path.exists(csv_path):
        open(csv_path, 'w', encoding='utf-8').close()

    count = 0
    while count < maxnews:
        try:
            response = await httpx_client.get(rss_link, timeout=10)
            response.raise_for_status()
        except httpx.RequestError as e:
            print(f"[izvestia] Ошибка запроса: {e}")
            await asyncio.sleep(10)
            continue
        except httpx.HTTPStatusError as e:
            print(f"[izvestia] Ошибка статуса: {e}")
            await asyncio.sleep(10)
            continue

        feed = feedparser.parse(response.text)

        for entry in feed.entries[::-1]:
            summary = entry.get('summary', '')
            title = entry.get('title', '')

            news_text = f'{title}\n{summary}'
            head = news_text[:n_test_chars].strip()

            if head in posted_q:
                continue

            with open(csv_path, 'a', encoding='utf-8', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([news_text])
                count += 1

            posted_q.appendleft(head)

            if count >= maxnews:
                break

        await asyncio.sleep(1)


async def main():
    posted_q = deque(maxlen=20)
    n_test_chars = 50

    async with httpx.AsyncClient() as httpx_client:
        await rss_parser(httpx_client, posted_q, n_test_chars, 'data/izvestia.csv', 500)


if __name__ == "__main__":
    os.makedirs("data", exist_ok=True)
    asyncio.run(main())
