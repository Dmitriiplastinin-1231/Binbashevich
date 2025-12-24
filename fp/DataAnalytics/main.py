import subprocess
import os

def run_pipeline(selected_telegram_groups, selected_vk_groups):
    scripts_dir = "./"

    tg_arg = ",".join(selected_telegram_groups) if selected_telegram_groups else ""
    vk_arg = ",".join(selected_vk_groups) if selected_vk_groups else ""

    scripts = [
        ("parser.py", ["--tg", tg_arg, "--vk", vk_arg]),
        ("analytics.py", []),
        ("analytics.py", ["--input", "totals", "--output", "networks_analytics"]),
        ("visualization.py", []),  # Flask
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
