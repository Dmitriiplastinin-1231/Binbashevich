import requests
import pandas as pd
import time
import os
import argparse

ACCESS_TOKEN = "b19316e2b19316e2b19316e21ab2a8db95bb193b19316e2d966b70ce89425b30a209ff6"
VERSION = "5.199"

parser = argparse.ArgumentParser(description="VK parser")
parser.add_argument("--groups", type=str, default="", help="Comma-separated list of VK groups to parse")
args = parser.parse_args()

vk_sources = ["kpru", "nws_ru", "rt_russian", "ndnews24", "vesti"]

if args.groups:
    selected_groups = [g.strip() for g in args.groups.split(",")]
    vk_sources = [g for g in vk_sources if g in selected_groups]

POSTS_PER_GROUP = 1000
MAX_COUNT = 100

def get_wall_posts(domain, total_count=POSTS_PER_GROUP):
    """Получает посты со стены сообщества с пагинацией."""
    url = "https://api.vk.com/method/wall.get"
    all_texts = []
    offset = 0

    while offset < total_count:
        params = {
            "access_token": ACCESS_TOKEN,
            "v": VERSION,
            "domain": domain,
            "count": MAX_COUNT,
            "offset": offset
        }
        r = requests.get(url, params=params)
        data = r.json()

        if "error" in data:
            print(f"Ошибка при получении {domain}: {data['error']['error_msg']}")
            break

        items = data["response"]["items"]
        if not items:
            break

        texts = [p["text"].replace("\n", " ").strip() for p in items if p["text"]]
        all_texts.extend(texts)

        offset += MAX_COUNT
        time.sleep(0.35)

    return all_texts[:total_count]

def main():
    os.makedirs("data", exist_ok=True)
    os.makedirs("totals", exist_ok=True)
    all_texts = []
    for group in vk_sources:
        print(f"Парсим посты из {group}...")
        texts = get_wall_posts(group)
        df = pd.DataFrame(texts, columns=["text"])
        df.to_csv(f"data/{group}.csv", sep=';', index=False, encoding="utf-8-sig")
        print(f"{group}: сохранено {len(texts)} постов")
        all_texts.extend(texts)

    df = pd.DataFrame(all_texts, columns=["text"])
    df.to_csv("totals/vkontakte.csv", sep=';', index=False, encoding="utf-8-sig")
    print(f"Готово! Всего постов: {len(all_texts)}.")

if __name__ == "__main__":
    main()
