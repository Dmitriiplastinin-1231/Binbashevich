import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton, QLabel, QTextEdit, QLineEdit, QGroupBox
)
from PyQt5.QtCore import QThread, pyqtSignal
import subprocess


class PipelineWorker(QThread):
    log_signal = pyqtSignal(str)
    finished_signal = pyqtSignal()

    def __init__(self, tg_groups, vk_groups):
        super().__init__()
        self.tg_groups = tg_groups
        self.vk_groups = vk_groups

    def run_script(self, script_name, args=None, capture=True):
        if args is None:
            args = []
        self.log_signal.emit(f"=== Запуск {script_name} {' '.join(args)} ===")
        result = subprocess.run(
            ["python3", script_name] + args,
            capture_output=capture,
            text=True,
        )
        if capture:
            if result.stdout:
                self.log_signal.emit(result.stdout)
            if result.stderr:
                self.log_signal.emit(f"Ошибка в {script_name}:\n{result.stderr}")
        self.log_signal.emit(f"--- {script_name} завершён с кодом {result.returncode} ---\n")
        return result

    def run(self):
        # Этап 1: параллельный парсинг всех 10 источников через parser.py
        tg_arg = ",".join(self.tg_groups) if self.tg_groups else ""
        vk_arg = ",".join(self.vk_groups) if self.vk_groups else ""

        parser_args = []
        if tg_arg:
            parser_args += ["--tg", tg_arg]
        if vk_arg:
            parser_args += ["--vk", vk_arg]

        self.run_script("parser.py", parser_args)

        self.log_signal.emit("\nПарсинг завершён. Переходим к аналитике.\n")

        # Этап 2: аналитика
        self.run_script("analytics.py")
        self.run_script("analytics.py", ["--input", "totals", "--output", "networks_analytics"])

        # Этап 3: визуализация
        subprocess.run(["python3", "visualization.py"])

        self.finished_signal.emit()


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Анализ данных из 10 источников")
        self.setMinimumWidth(600)
        layout = QVBoxLayout()

        # --- Telegram группы (текстовое поле) ---
        tg_group = QGroupBox("Telegram-группы")
        tg_layout = QVBoxLayout()
        tg_layout.addWidget(QLabel("Введите названия групп через запятую:"))
        self.tg_input = QLineEdit()
        self.tg_input.setPlaceholderText("Например: Mash, Фонтанка SPB Online, РИА Новости")
        tg_layout.addWidget(self.tg_input)
        tg_group.setLayout(tg_layout)
        layout.addWidget(tg_group)

        # --- VK группы (текстовое поле) ---
        vk_group = QGroupBox("VK-группы")
        vk_layout = QVBoxLayout()
        vk_layout.addWidget(QLabel("Введите short_name групп через запятую:"))
        self.vk_input = QLineEdit()
        self.vk_input.setPlaceholderText("Например: kpru, nws_ru, rt_russian, ndnews24, vesti")
        vk_layout.addWidget(self.vk_input)
        vk_group.setLayout(vk_layout)
        layout.addWidget(vk_group)

        # --- Информация о дополнительных источниках ---
        info_group = QGroupBox("Автоматические источники (8 шт.)")
        info_layout = QVBoxLayout()
        sources_label = QLabel(
            "RBC, VC.ru, Habr, Lenta.ru, ТАСС, Коммерсантъ, Газета.ру, Известия\n"
            "Эти источники парсятся автоматически при запуске."
        )
        info_layout.addWidget(sources_label)
        info_group.setLayout(info_layout)
        layout.addWidget(info_group)

        self.start_button = QPushButton("Запустить (10 источников параллельно)")
        layout.addWidget(self.start_button)

        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        layout.addWidget(self.log_output)

        self.setLayout(layout)
        self.start_button.clicked.connect(self.start_pipeline)

    def start_pipeline(self):
        tg_text = self.tg_input.text().strip()
        vk_text = self.vk_input.text().strip()

        tg_groups = [g.strip() for g in tg_text.split(",") if g.strip()] if tg_text else []
        vk_groups = [g.strip() for g in vk_text.split(",") if g.strip()] if vk_text else []

        self.log_output.clear()
        self.log_output.append(f"Telegram группы: {tg_groups}")
        self.log_output.append(f"VK группы: {vk_groups}")
        self.log_output.append(f"+ 8 автоматических источников\n")

        self.worker = PipelineWorker(tg_groups, vk_groups)
        self.worker.log_signal.connect(self.update_log)
        self.worker.finished_signal.connect(self.pipeline_finished)
        self.start_button.setEnabled(False)
        self.worker.start()

    def update_log(self, text):
        self.log_output.append(text)

    def pipeline_finished(self):
        self.log_output.append("=== Все скрипты завершены ===")
        self.start_button.setEnabled(True)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
