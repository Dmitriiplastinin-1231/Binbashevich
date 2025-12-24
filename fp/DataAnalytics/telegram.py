import re
import os
from pathlib import Path
import asyncio
import csv
from telethon import TelegramClient
from telethon.tl.functions.messages import GetDialogsRequest, GetHistoryRequest
from telethon.tl.types import InputPeerEmpty, Channel
import argparse

OUTPUT_DIR = Path("./data")
OUTPUT_DIR.mkdir(exist_ok=True)

TOTAL_OUTPUT = Path("./totals")
TOTAL_OUTPUT.mkdir(exist_ok=True)

api_id = 22260567
api_hash = "eebbbb9fbf850fb94fee8b5658132c75"
phone = "+79939583021"

client = TelegramClient(phone, api_id, api_hash)

parser = argparse.ArgumentParser(description="Telegram parser")
parser.add_argument("--groups", type=str, default="", help="Comma-separated list of groups to parse")
args = parser.parse_args()

telegram_sources = ['Фонтанка SPB Online', 'РИА Новости', 'Топор. Экономика.', 'Mash', 'Прямой Эфир • Новости']

if args.groups:
    selected_groups = [g.strip() for g in args.groups.split(",")]
    telegram_sources = [g for g in telegram_sources if g in selected_groups]

limit = 100
total_count_limit = 5000

async def get_channels():
    groups = []
    seen_id = []
    last_date = None
    chunk_size = 200

    result = await client(GetDialogsRequest(
        offset_date=last_date,
        offset_id=0,
        offset_peer=InputPeerEmpty(),
        limit=chunk_size,
        hash=0
    ))

    for chat in result.chats:
        try:
            if isinstance(chat, Channel) and chat.id not in seen_id and chat.title in telegram_sources:
                groups.append(chat)
                seen_id.append(chat.id)
        except Exception:
            continue

    return groups

async def channel_parsing(channel, channel_limit):
    messages = []
    offset_id = 0
    messages_count = 0

    while True:
        history = await client(GetHistoryRequest(
            peer=channel,
            offset_id=offset_id,
            offset_date=None,
            add_offset=0,
            limit=limit,
            max_id=0,
            min_id=0,
            hash=0
        ))
        if not history.messages:
            break

        for m in history.messages:
            if m.message:
                messages.append(m.message)
                messages_count += 1

        offset_id = history.messages[-1].id
        if messages_count >= channel_limit:
            messages = messages[:channel_limit]
            break

    print(f'Канал {channel.title} обработан.')
    return messages

async def main():
    await client.start()
    groups = await get_channels()
    channel_limit = total_count_limit // len(groups)

    tasks = [channel_parsing(ch, channel_limit) for ch in groups]
    results = await asyncio.gather(*tasks)
    all_messages = []
    for i, (channel, messages) in enumerate(zip(groups, results)):
        safe_name = re.sub(r'[\\/*?:"<>|]', "_", channel.title)
        filepath = OUTPUT_DIR / f"{safe_name}.csv"
        
        with open(filepath, "w", encoding="utf-8-sig", newline='') as f:
            writer = csv.writer(f, delimiter=";", lineterminator="\n")
            writer.writerows([[m] for m in messages])
        all_messages.extend(messages)

    filepath = TOTAL_OUTPUT / "telegram.csv"
    with open(filepath, "w", encoding="utf-8-sig") as f:
        writer = csv.writer(f, delimiter=";", lineterminator="\n")
        writer.writerows([[m] for m in all_messages])
    

    print('Парсинг сообщений группы успешно выполнен.')
asyncio.run(main())