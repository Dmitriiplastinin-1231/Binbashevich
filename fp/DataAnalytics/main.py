import subprocess
import os

def run_pipeline(selected_telegram_groups, selected_vk_groups):
    """Запуск полного пайплайна: парсинг 10 источников -> аналитика -> визуализация."""
    scripts_dir = "./"

    tg_arg = ",".join(selected_telegram_groups) if selected_telegram_groups else ""
    vk_arg = ",".join(selected_vk_groups) if selected_vk_groups else ""

    # parser.py параллельно запускает все 10 источников
    # (telegram, vkontakte, rbc, vc, habr, lentaru, tass, kommersant, gazeta, izvestia)
    parser_args = []
    if tg_arg:
        parser_args += ["--tg", tg_arg]
    if vk_arg:
        parser_args += ["--vk", vk_arg]

    scripts = [
        ("parser.py", parser_args),                                      # 10 парсеров параллельно + uniter
        ("analytics.py", []),                                             # аналитика по отдельным источникам
        ("analytics.py", ["--input", "totals", "--output", "networks_analytics"]),  # аналитика по сетям
        ("visualization.py", []),                                         # Flask-визуализация
    ]

    for i, (script, args) in enumerate(scripts):
        print(f"=== Запуск {script} {' '.join(args)} ===")

        capture = False if script == "visualization.py" else True

        result = subprocess.run(
            ["python", os.path.join(scripts_dir, script)] + args,
            capture_output=not capture,
            text=True,
            cwd=scripts_dir,
            env=os.environ,
        )

        if capture:
            if result.stdout:
                print(result.stdout)
            if result.stderr:
                print(f"Ошибка в {script}:\n{result.stderr}")

        print(f"--- {script} завершён с кодом {result.returncode} ---\n")


if __name__ == "__main__":
    tg_groups = ["Mash", "Фонтанка SPB Online"]
    vk_groups = ["kpru", "nws_ru"]
    run_pipeline(tg_groups, vk_groups)
