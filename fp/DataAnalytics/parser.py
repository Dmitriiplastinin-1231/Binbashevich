import subprocess
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import argparse

# === Аргументы через argparse ===
parser = argparse.ArgumentParser(description="Parser for 10 data sources (parallel)")
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
def run_script(script_name, script_args=None):
    if script_args is None:
        script_args = []
    print(f"Запуск {script_name} ...")
    start_time = time.perf_counter()
    result = subprocess.run(
        ["python", script_name] + script_args,
        capture_output=True, text=True
    )
    if result.returncode == 0:
        print(f"{script_name} завершён успешно.")
    else:
        print(f"Ошибка в {script_name}:\n{result.stderr}")
    elapsed_time = time.perf_counter() - start_time
    print(f"Elapsed time: {elapsed_time:.2f} seconds")
    return result


# === Параллельный запуск всех 10 источников ===
# Каждый источник обрабатывается в отдельном потоке (по ТЗ)
tg_groups = ",".join(selected_telegram_groups)
vk_groups = ",".join(selected_vk_groups)

# Список из 10 источников: (script, args)
all_sources = [
    ("telegram.py", ["--groups", tg_groups] if tg_groups else []),   # 1. Telegram
    ("vkontakte.py", ["--groups", vk_groups] if vk_groups else []),  # 2. VKontakte
    ("rbc.py", []),                                                   # 3. RBC
    ("vc.py", []),                                                    # 4. VC.ru
    ("habr.py", []),                                                  # 5. Habr
    ("lentaru.py", []),                                               # 6. Lenta.ru
    ("tass.py", []),                                                  # 7. ТАСС
    ("kommersant.py", []),                                            # 8. Коммерсантъ
    ("gazeta.py", []),                                                # 9. Газета.ру
    ("izvestia.py", []),                                              # 10. Известия
]

print(f"\nЗапуск параллельного парсинга {len(all_sources)} источников...\n")

with ThreadPoolExecutor(max_workers=len(all_sources)) as executor:
    futures = {
        executor.submit(run_script, script, script_args): script
        for script, script_args in all_sources
    }
    for future in as_completed(futures):
        script = futures[future]
        try:
            future.result()
        except Exception as e:
            print(f"Исключение при выполнении {script}: {e}")

print("\nВсе 10 источников обработаны. Запуск объединения данных...\n")

# === Объединение результатов ===
run_script('uniter.py')

print("\nВсе скрипты успешно выполнены!")
