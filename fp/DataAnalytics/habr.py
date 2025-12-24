#!/usr/bin/env python3
# habr_parser.py
"""
Многопоточный парсер статей с habr.com (актуально на 2025 год)
Сохраняет текст статей (без заголовков) в CSV без заголовочной строки.
"""

import csv
import sys
import time
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Optional, Set
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup
import os

# Константы
MAX_WORKERS = 12
REQUEST_TIMEOUT = 10
HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; HabrParser/1.0)",
    "Accept-Language": "ru,en;q=0.9",
}


def fetch(url: str, session: Optional[requests.Session] = None) -> Optional[str]:
    s = session or requests
    try:
        r = s.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
        r.raise_for_status()
        r.encoding = "utf-8"
        return r.text
    except Exception as e:
        print(f"[ERROR] {url}: {e}", file=sys.stderr)
        return None


def extract_links_from_page(html: str, base: str = "https://habr.com") -> List[str]:
    """Извлекает ссылки на статьи с одной страницы ленты /ru/all/"""
    soup = BeautifulSoup(html, "html.parser")
    links = set()

    # В 2025 Habr использует структуру:
    # <a class="tm-title__link" href="/ru/articles/123456/">
    for a in soup.select("a.tm-title__link[href]"):
        href = a["href"]
        full_url = urljoin(base, href)
        links.add(full_url)

    # Также захватываем ссылки компаний (например, /ru/companies/yandex/articles/...)
    for a in soup.select("a[href^='/ru/companies/']"):
        href = a["href"]
        if "/articles/" in href:
            links.add(urljoin(base, href))

    return list(links)


def extract_article_text(html: str) -> str:
    """Извлекает текст статьи без заголовка"""
    soup = BeautifulSoup(html, "html.parser")

    # Основное тело статьи (tm-article-body или article-formatted-body)
    body = soup.select_one("div.tm-article-body") or soup.select_one("div.article-formatted-body")
    if not body:
        return ""

    # Извлекаем только текст
    text = body.get_text(separator="\n", strip=True)

    # Удаляем повторяющиеся переносы
    while "\n\n\n" in text:
        text = text.replace("\n\n\n", "\n\n")
    return text.strip()


def collect_article_links(base_url: str, pages: int = 3) -> Set[str]:
    """Проходит по страницам ленты и собирает все ссылки на статьи"""
    session = requests.Session()
    all_links = set()

    for page_num in range(1, pages + 1):
        page_url = f"{base_url}page{page_num}/"
        print(f"[INFO] Crawling {page_url}", file=sys.stderr)
        html = fetch(page_url, session)
        if not html:
            continue
        links = extract_links_from_page(html, base=base_url)
        print(f"[INFO] Found {len(links)} links on page {page_num}", file=sys.stderr)
        all_links.update(links)
        time.sleep(0.3)

    return all_links


def fetch_article(url: str, session: requests.Session) -> Optional[str]:
    html = fetch(url, session)
    if not html:
        return None
    text = extract_article_text(html)
    return text if text else None


def main():
    parser = argparse.ArgumentParser(description="Habr article parser -> CSV (texts only, no header row)")
    parser.add_argument("--out", type=str, default="data/habr.csv", help="Output CSV file")
    parser.add_argument("--base", type=str, default="https://habr.com/ru/all/", help="Base page to crawl")
    parser.add_argument("--pages", type=int, default=3, help="Number of pages to crawl")
    args = parser.parse_args()


    urls = collect_article_links(args.base, args.pages)
    print(f"[INFO] Total {len(urls)} article links collected", file=sys.stderr)
    if not urls:
        print("[WARN] No articles found. Exiting.", file=sys.stderr)
        return

    session = requests.Session()
    results = []

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(fetch_article, url, session): url for url in urls}
        for future in as_completed(futures):
            url = futures[future]
            try:
                text = future.result()
                if text:
                    results.append(text)
                    print(f"[OK] Parsed {url} ({len(text)} chars)", file=sys.stderr)
                else:
                    print(f"[SKIP] No text from {url}", file=sys.stderr)
            except Exception as e:
                print(f"[ERROR] {url}: {e}", file=sys.stderr)

    # Сохраняем в CSV без заголовков
    with open(args.out, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        for text in results:
            writer.writerow([text])

    print(f"[DONE] Saved {len(results)} articles to {args.out}", file=sys.stderr)


if __name__ == "__main__":
    os.makedirs("data", exist_ok=True)
    main()

# python habr.py --out data/articles.csv --pages 3