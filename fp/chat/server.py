import asyncio
import os
from urllib.parse import quote

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)
CLIENTS = {}
ROOMS = {}

WELCOME = """Добро пожаловать в чат!
В нашем чате вы можете хорошо провести время со своими друзьями. Например общаться в комнате, общаться в личных сообщениях.А так же придумать себе смешное имя :) УДАЧИ!!!
"""

async def handle_client(reader, writer):
    writer.write(WELCOME.encode('utf-8'))
    await writer.drain()
    
    CLIENTS[writer] = {"nick": None, "room": None}
    addr = writer.get_extra_info("peername")
    print(f"New connection: {addr}")

    try:
        while True:
            data = await reader.readline()
            if not data:
                break
            msg = data.decode('utf-8').strip()
            if not msg:
                continue

            if msg.startswith("/nick"):
                parts = msg.split(maxsplit=1)
                if len(parts) < 2:
                    writer.write("Использование: /nick <имя>\n".encode('utf-8'))
                    await writer.drain()
                    continue
                nick = parts[1].strip()
                if not nick:
                    writer.write("Имя не может быть пустым\n".encode('utf-8'))
                    await writer.drain()
                    continue
                if any(info["nick"] == nick for info in CLIENTS.values()):
                    writer.write("Этот ник уже занят\n".encode('utf-8'))
                    await writer.drain()
                    continue
                CLIENTS[writer]["nick"] = nick
                writer.write(f"Псевдоним установлен: {nick}\n".encode('utf-8'))
                await writer.drain()
                continue

            elif msg.startswith("/sendfile"):
                parts = msg.split(maxsplit=2)
                if len(parts) < 2:
                    writer.write("Использование: /sendfile <filename>\n".encode('utf-8'))
                    await writer.drain()
                    continue
                filename = parts[1]
                writer.write(f"Отправляйте файл {filename}\n".encode('utf-8'))
                await writer.drain()

                room = CLIENTS[writer]["room"]
                if not room:
                    writer.write("Сначала войдите в комнату через /join\n".encode('utf-8'))
                    await writer.drain()
                    continue

                file_data = b""
                while True:
                    chunk = await reader.read(1024)
                    if not chunk:
                        break
                    file_data += chunk
                    if len(chunk) < 1024:
                        break

                safe_filename = f"{CLIENTS[writer]['nick']}_{filename}"
                file_path = os.path.join(UPLOAD_DIR, safe_filename)
                with open(file_path, "wb") as f:
                    f.write(file_data)

                file_url = f"http://127.0.0.1:8080/files/{quote(safe_filename)}"

                for w in ROOMS[room]["members"]:
                    w.write(f"[Файл] {CLIENTS[writer]['nick']} отправил файл: {filename}. Скачать: {file_url}\n".encode('utf-8'))
                    await w.drain()

                writer.write(f"Файл {filename} загружен. Ссылка: {file_url}\n".encode('utf-8'))
                await writer.drain()

            elif msg.startswith("/join"):
                parts = msg.split(maxsplit=1)
                if len(parts) < 2:
                    writer.write("Использование: /join <room>\n".encode('utf-8'))
                    await writer.drain()
                    continue
                room = parts[1]
                old_room = CLIENTS[writer]["room"]
                if old_room:
                    ROOMS[old_room]["members"].discard(writer)
                CLIENTS[writer]["room"] = room
                if room not in ROOMS:
                    ROOMS[room] = {"members": set()}
                ROOMS[room]["members"].add(writer)
                writer.write(f"Вы вошли в комнату {room}\n".encode('utf-8'))
                await writer.drain()

            elif msg.startswith("/rooms"):
                room_list = ", ".join(ROOMS.keys())
                writer.write(f"Комнаты: {room_list}\n".encode('utf-8'))
                await writer.drain()

            elif msg.startswith("/pm"):
                parts = msg.split(maxsplit=2)
                if len(parts) < 3:
                    writer.write("Использование: /pm <nick> <msg>\n".encode('utf-8'))
                    await writer.drain()
                    continue
                target_nick, message = parts[1], parts[2]
                found = False
                for w, info in CLIENTS.items():
                    if info["nick"] == target_nick:
                        w.write(f"[PM от {CLIENTS[writer]['nick']}] {message}\n".encode('utf-8'))
                        await w.drain()
                        writer.write(f"[PM к {target_nick}] {message}\n".encode('utf-8'))
                        await writer.drain()
                        found = True
                        break
                if not found:
                    writer.write("Пользователь не найден\n".encode('utf-8'))
                    await writer.drain()

            elif msg.startswith("/quit"):
                break

            else:
                room = CLIENTS[writer]["room"]
                nick = CLIENTS[writer]["nick"] or "Anon"
                if room and room in ROOMS:
                    for w in ROOMS[room]["members"]:
                        w.write(f"[{nick}] {msg}\n".encode('utf-8'))
                        await w.drain()
                else:
                    writer.write("Сначала войдите в комнату через /join\n".encode('utf-8'))
                    await writer.drain()

    except Exception as e:
        print(f"Ошибка с клиентом {addr}: {e}")

    room = CLIENTS[writer]["room"]
    if room and room in ROOMS:
        ROOMS[room]["members"].discard(writer)
    del CLIENTS[writer]
    writer.close()
    await writer.wait_closed()
    print(f"Connection closed: {addr}")

async def main(host="127.0.0.1", port=8888):
    server = await asyncio.start_server(handle_client, host, port)
    print(f"Сервер слушает {host}:{port}")
    async with server:
        await server.serve_forever()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Сервер остановлен")