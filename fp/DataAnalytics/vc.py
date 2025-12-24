from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from concurrent.futures import ThreadPoolExecutor, as_completed
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
import time
import requests
import csv
import os

# Настройка headless Chrome
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=1920,1080")

driver = webdriver.Chrome(options=chrome_options)
driver.get("https://vc.ru/popular")

link_lst = set()
links_needed = 200  # сколько ссылок хотим собрать
scroll_pause = 0.5   # пауза между прокрутками

last_height = driver.execute_script("return document.body.scrollHeight")

while len(link_lst) < links_needed:
    # Прокрутка вниз
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(scroll_pause)

    # Сбор ссылок
    articles = driver.find_elements(By.CSS_SELECTOR, 'div.content__body a')
    for a in articles:
        link = a.get_attribute('href')
        if link:
            link_lst.add(link)

    # Проверка: если страница больше не растёт, заканчиваем
    new_height = driver.execute_script("return document.body.scrollHeight")
    if new_height == last_height:
        print("Больше новых элементов нет")
        break
    last_height = new_height
    print(f"Собрано ссылок: {len(link_lst)}")

driver.quit()

link_lst = list(link_lst)  # преобразуем set в список

def get_article_text(url):
    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code != 200:
            print(f"Ошибка {resp.status_code} на {url}")
            return None
        soup = BeautifulSoup(resp.text, 'html.parser')
        #print(soup.prettify())
        # На vc.ru текст статьи обычно внутри div с классом 'article__content'
        content_div = soup.find('div', class_='content__body')
        if not content_div:
            return None
        paragraphs = content_div.find_all('p')
        text = "\n".join(p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True))
        return text
    except Exception as e:
        print(f"Ошибка на {url}: {e}")
        return None

num_threads = 10
all_texts = []

with ThreadPoolExecutor(max_workers=num_threads) as executor:
    futures = {executor.submit(get_article_text, url): url for url in link_lst}
    for future in as_completed(futures):
        text = future.result()
        if text:
            all_texts.append(text)

# Записываем в CSV, один столбец, без заголовков
os.makedirs("data", exist_ok=True)
with open('data/vc.csv', 'w', encoding='utf-8', newline='') as f:
    writer = csv.writer(f)
    for text in all_texts:
        writer.writerow([text])

print(f"Готово! Сохранено {len(all_texts)} статей.")