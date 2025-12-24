import asyncio
import pytest
from server import main as server_main

HOST = "127.0.0.1"
PORT = 8888
TIMEOUT = 3  # таймаут для чтения с сервера

@pytest.fixture
async def run_server():
    task = asyncio.create_task(server_main(host=HOST, port=PORT))
    try:
        # даём серверу 2 секунды на старт
        await asyncio.wait_for(asyncio.sleep(2), timeout=5)
        yield
    finally:
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass

async def connect_client():
    reader, writer = await asyncio.open_connection(HOST, PORT)
    # пропускаем приветствие (несколько строк)
    for _ in range(10):
        try:
            line = await asyncio.wait_for(reader.readline(), timeout=TIMEOUT)
        except asyncio.TimeoutError:
            break
    return reader, writer

# ------------------- Тесты -------------------

@pytest.mark.asyncio
async def test_nick_and_join(run_server):
    r, w = await connect_client()
    print("Тест /nick и /join: подключение клиента")

    w.write("/nick Tester\n".encode())
    await w.drain()
    resp = await asyncio.wait_for(r.readline(), timeout=TIMEOUT)
    assert "Псевдоним установлен: Tester" in resp.decode()

    w.write("/join room1\n".encode())
    await w.drain()
    resp = await asyncio.wait_for(r.readline(), timeout=TIMEOUT)
    assert "Вы вошли в комнату room1" in resp.decode() 

    w.write("/quit\n".encode())
    await w.drain()
    w.close(); await w.wait_closed()

@pytest.mark.asyncio
async def test_message_broadcast(run_server):
    r1, w1 = await connect_client()
    r2, w2 = await connect_client()
    print("Тест рассылки сообщений: подключение двух клиентов")

    w1.write("/nick Alice\n".encode()); await w1.drain(); await asyncio.wait_for(r1.readline(), timeout=TIMEOUT)
    w1.write("/join room1\n".encode()); await w1.drain(); await asyncio.wait_for(r1.readline(), timeout=TIMEOUT)

    w2.write("/nick Bob\n".encode()); await w2.drain(); await asyncio.wait_for(r2.readline(), timeout=TIMEOUT)
    w2.write("/join room1\n".encode()); await w2.drain(); await asyncio.wait_for(r2.readline(), timeout=TIMEOUT)

    w1.write("Hello Bob\n".encode()); await w1.drain()
    msg = await asyncio.wait_for(r2.readline(), timeout=TIMEOUT)
    assert "[Alice] Hello Bob" in msg.decode()

    w1.write("/quit\n".encode()); w2.write("/quit\n".encode())
    await w1.drain(); await w2.drain()
    w1.close(); w2.close()
    await w1.wait_closed(); await w2.wait_closed()

@pytest.mark.asyncio
async def test_private_message(run_server):
    r1, w1 = await connect_client()
    r2, w2 = await connect_client()
    print("Тест личных сообщений")

    w1.write("/nick Alice\n".encode()); await w1.drain(); await asyncio.wait_for(r1.readline(), timeout=TIMEOUT)
    w2.write("/nick Bob\n".encode()); await w2.drain(); await asyncio.wait_for(r2.readline(), timeout=TIMEOUT)

    w1.write("/pm Bob Привет\n".encode()); await w1.drain()
    msg = await asyncio.wait_for(r2.readline(), timeout=TIMEOUT)
    assert "[PM от Alice]" in msg.decode()
    confirm = await asyncio.wait_for(r1.readline(), timeout=TIMEOUT)
    assert "Личное сообщение отправлено" in confirm.decode()

    w1.write("/quit\n".encode()); w2.write("/quit\n".encode())
    await w1.drain(); await w2.drain()
    w1.close(); w2.close()
    await w1.wait_closed(); await w2.wait_closed()