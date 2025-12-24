import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QCheckBox, QPushButton, QLabel, QTextEdit
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
        # --- Этап 1: параллельно Telegram и VK ---
        parallel_scripts = []
        if self.tg_groups:
            parallel_scripts.append(("telegram.py", ["--groups", ",".join(self.tg_groups)]))
        if self.vk_groups:
            parallel_scripts.append(("vkontakte.py", ["--groups", ",".join(self.vk_groups)]))

        for script, args in parallel_scripts:
            self.run_script(script, args)

        self.log_signal.emit("\nПервый этап завершён. Переходим к последовательному запуску.\n")

        # --- Этап 2: последовательные скрипты ---
        sequential_scripts = ["rbc.py", "vc.py", "habr.py", "uniter.py"]
        for script in sequential_scripts:
            self.run_script(script)

        # --- Этап 3: аналитика и визуализация ---
        self.run_script("analytics.py")
        self.run_script("analytics.py", ["--input", "totals", "--output", "networks_analytics"])
        subprocess.run(["python3", "visualization.py"])

        self.finished_signal.emit()


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Парсер Sources")
        layout = QVBoxLayout()

        layout.addWidget(QLabel("Выберите Telegram-группы:"))
        self.telegram_checkbox = []
        telegram_sources = ['Фонтанка SPB Online', 'РИА Новости', 'Топор. Экономика.', 'Mash', 'Прямой Эфир • Новости']
        for source in telegram_sources:
            cb = QCheckBox(source)
            layout.addWidget(cb)
            self.telegram_checkbox.append(cb)

        layout.addWidget(QLabel("Выберите VK-группы:"))
        self.vk_checkbox = []
        vk_sources = ["kpru", "nws_ru", "rt_russian", "ndnews24", 'vesti']
        for source in vk_sources:
            cb = QCheckBox(source)
            layout.addWidget(cb)
            self.vk_checkbox.append(cb)

        self.start_button = QPushButton("Запустить")
        layout.addWidget(self.start_button)

        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        layout.addWidget(self.log_output)

        self.setLayout(layout)
        self.start_button.clicked.connect(self.start_pipeline)

    def start_pipeline(self):
        tg_groups = [cb.text() for cb in self.telegram_checkbox if cb.isChecked()]
        vk_groups = [cb.text() for cb in self.vk_checkbox if cb.isChecked()]

        if not tg_groups and not vk_groups:
            self.log_output.append("⚠ Нужно выбрать хотя бы одну группу.")
            return

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
