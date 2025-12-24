import subprocess
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import argparse

# === Аргументы через argparse ===
parser = argparse.ArgumentParser(description="Parser for Telegram and VK sources")
parser.add_argument(
    "--tg", type=str, default="", help="Comma-separated list of Telegram groups to parse"
)
parser.add_argument(
    "--vk", type=str, default="", help="Comma-separated list of VK groups to parse"
)
args = parser.parse_args()

selected_telegram_groups = [g.strip() for g in args.tg.split(",") if g.strip()]
selected_vk_groups = [g.strip() for g in args.vk.split(",") if g.strip()]

print("Выбраны Telegram группы:", selected_telegram_groups)
print("Выбраны VK группы:", selected_vk_groups)

# Функция для запуска скрипта
def run_script(script_name, args=None):
    print(f"Запуск {script_name} ...")
    start_time = time.perf_counter()
    result = subprocess.run(["python", script_name] + args, capture_output=True, text=True)
    if result.returncode == 0:
        print(f"{script_name} завершён успешно.")
    else:
        print(f"Ошибка в {script_name}:\n{result.stderr}")
    end_time = time.perf_counter()
    elapsed_time = end_time - start_time
    print(f"Elapsed time: {elapsed_time:.2f} seconds")
    return result

# === Этап 1: многопоточно запускаем telegram.py и vkontakte.py ===
parallel_scripts = ["telegram.py", "vkontakte.py"]

tg_groups = ",".join(selected_telegram_groups)
vk_groups = ",".join(selected_vk_groups)

with ThreadPoolExecutor(max_workers=2) as executor:
    futures = [
        executor.submit(
            run_script,
            "telegram.py",
            ["--groups", tg_groups] if tg_groups else []
        ),
        executor.submit(
            run_script,
            "vkontakte.py",
            ["--groups", vk_groups] if vk_groups else []
        ),
    ]
    for future in as_completed(futures):
        future.result()

print("\n Первый этап завершён. Переходим к последовательному запуску.\n")

# === Этап 2: последовательно запускаем rbc.py, vc.py, habr.py ===
sequential_scripts = ["rbc.py", "vc.py", "habr.py"]

for script in sequential_scripts:
    run_script(script)
run_script('uniter.py')
print("\n Все скрипты успешно выполнены!")
