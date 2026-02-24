import tkinter as tk
from tkinter import ttk, scrolledtext
import subprocess
import threading


def run_script(script_name, args=None, log_func=None):
    """Запуск скрипта и логирование результата."""
    if args is None:
        args = []
    if log_func:
        log_func(f"=== Запуск {script_name} {' '.join(args)} ===\n")
    result = subprocess.run(
        ["python3", script_name] + args,
        capture_output=True,
        text=True,
    )
    if log_func:
        if result.stdout:
            log_func(result.stdout)
        if result.stderr:
            log_func(f"Ошибка в {script_name}:\n{result.stderr}\n")
        log_func(f"--- {script_name} завершён с кодом {result.returncode} ---\n\n")
    return result


def run_pipeline(tg_groups, vk_groups, log_func, on_finish):
    """Запуск пайплайна в отдельном потоке."""
    tg_arg = ",".join(tg_groups) if tg_groups else ""
    vk_arg = ",".join(vk_groups) if vk_groups else ""

    parser_args = []
    if tg_arg:
        parser_args += ["--tg", tg_arg]
    if vk_arg:
        parser_args += ["--vk", vk_arg]

    # Этап 1: параллельный парсинг 10 источников
    run_script("parser.py", parser_args, log_func)
    log_func("\nПарсинг завершён. Переходим к аналитике.\n\n")

    # Этап 2: аналитика
    run_script("analytics.py", [], log_func)
    run_script("analytics.py", ["--input", "totals", "--output", "networks_analytics"], log_func)

    # Этап 3: визуализация
    run_script("visualization.py", [], log_func)

    log_func("=== Все скрипты завершены ===\n")
    on_finish()


class MainWindow:
    def __init__(self, root):
        self.root = root
        root.title("Анализ данных из 10 источников")
        root.geometry("700x600")
        root.resizable(True, True)

        main_frame = ttk.Frame(root, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # --- Telegram группы ---
        tg_frame = ttk.LabelFrame(main_frame, text="Telegram-группы", padding=5)
        tg_frame.pack(fill=tk.X, pady=(0, 5))

        ttk.Label(tg_frame, text="Введите названия групп через запятую:").pack(anchor=tk.W)
        self.tg_input = ttk.Entry(tg_frame)
        self.tg_input.pack(fill=tk.X, pady=2)
        self.tg_input.insert(0, "Mash, Фонтанка SPB Online, РИА Новости")

        # --- VK группы ---
        vk_frame = ttk.LabelFrame(main_frame, text="VK-группы", padding=5)
        vk_frame.pack(fill=tk.X, pady=(0, 5))

        ttk.Label(vk_frame, text="Введите short_name групп через запятую:").pack(anchor=tk.W)
        self.vk_input = ttk.Entry(vk_frame)
        self.vk_input.pack(fill=tk.X, pady=2)
        self.vk_input.insert(0, "kpru, nws_ru, rt_russian, ndnews24, vesti")

        # --- Информация об автоматических источниках ---
        info_frame = ttk.LabelFrame(main_frame, text="Автоматические источники (8 шт.)", padding=5)
        info_frame.pack(fill=tk.X, pady=(0, 5))

        ttk.Label(
            info_frame,
            text="RBC, VC.ru, Habr, Lenta.ru, ТАСС, Коммерсантъ, Газета.ру, Известия\n"
                 "Эти источники парсятся автоматически при запуске.",
            wraplength=650
        ).pack(anchor=tk.W)

        # --- Кнопка запуска ---
        self.start_button = ttk.Button(
            main_frame,
            text="Запустить (10 источников параллельно)",
            command=self.start_pipeline
        )
        self.start_button.pack(fill=tk.X, pady=5)

        # --- Лог ---
        self.log_output = scrolledtext.ScrolledText(main_frame, height=15, state=tk.DISABLED)
        self.log_output.pack(fill=tk.BOTH, expand=True)

    def append_log(self, text):
        """Потокобезопасная запись в лог."""
        def _append():
            self.log_output.config(state=tk.NORMAL)
            self.log_output.insert(tk.END, text)
            self.log_output.see(tk.END)
            self.log_output.config(state=tk.DISABLED)
        self.root.after(0, _append)

    def on_finish(self):
        """Вызывается по завершении пайплайна."""
        self.root.after(0, lambda: self.start_button.config(state=tk.NORMAL))

    def start_pipeline(self):
        tg_text = self.tg_input.get().strip()
        vk_text = self.vk_input.get().strip()

        tg_groups = [g.strip() for g in tg_text.split(",") if g.strip()] if tg_text else []
        vk_groups = [g.strip() for g in vk_text.split(",") if g.strip()] if vk_text else []

        # Очистка лога
        self.log_output.config(state=tk.NORMAL)
        self.log_output.delete("1.0", tk.END)
        self.log_output.config(state=tk.DISABLED)

        self.append_log(f"Telegram группы: {tg_groups}\n")
        self.append_log(f"VK группы: {vk_groups}\n")
        self.append_log("+ 8 автоматических источников\n\n")

        self.start_button.config(state=tk.DISABLED)

        # Запуск в фоновом потоке, чтобы GUI не зависал
        t = threading.Thread(
            target=run_pipeline,
            args=(tg_groups, vk_groups, self.append_log, self.on_finish),
            daemon=True
        )
        t.start()


if __name__ == "__main__":
    root = tk.Tk()
    app = MainWindow(root)
    root.mainloop()
