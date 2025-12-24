"""
Графический интерфейс для системы обнаружения и блокировки сетевого трафика.
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import logging
from datetime import datetime
import json

from traffic_analyzer import TrafficAnalyzer
from firewall_manager import FirewallManager
from traffic_monitor import TrafficMonitor


class TrafficMonitorGUI:
    """Графический интерфейс для мониторинга трафика."""
    
    def __init__(self, root):
        self.root = root
        self.root.title("🛡️ Система обнаружения и блокировки сетевого трафика")
        self.root.geometry("1200x800")
        self.root.configure(bg="#1e293b")
        
        # Инициализация компонентов
        self.analyzer = TrafficAnalyzer()
        self.firewall = FirewallManager()
        self.monitor = TrafficMonitor(
            self.analyzer,
            self.firewall,
            callback=self.on_packet_event
        )
        
        # Настройка логирования
        self.setup_logging()
        
        # Создание интерфейса
        self.create_widgets()
        
        # Обновление статистики
        self.update_statistics()
        
    def setup_logging(self):
        """Настройка логирования."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        
    def create_widgets(self):
        """Создает виджеты интерфейса."""
        
        # Стили
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('TFrame', background='#1e293b')
        style.configure('TLabel', background='#1e293b', foreground='#e2e8f0', font=('Arial', 10))
        style.configure('Title.TLabel', font=('Arial', 14, 'bold'), foreground='#a5b4fc')
        style.configure('TButton', font=('Arial', 10, 'bold'))
        
        # Заголовок
        header_frame = ttk.Frame(self.root)
        header_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(
            header_frame,
            text="🛡️ Система обнаружения и блокировки подозрительного трафика",
            style='Title.TLabel'
        ).pack()
        
        # Основной контейнер
        main_container = ttk.Frame(self.root)
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Левая панель - управление и статистика
        left_panel = ttk.Frame(main_container)
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=False, padx=(0, 5))
        
        # Панель управления
        self.create_control_panel(left_panel)
        
        # Статистика
        self.create_statistics_panel(left_panel)
        
        # Заблокированные IP
        self.create_blocked_ips_panel(left_panel)
        
        # Правая панель - логи и события
        right_panel = ttk.Frame(main_container)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # События
        self.create_events_panel(right_panel)
        
        # Логи
        self.create_logs_panel(right_panel)
        
    def create_control_panel(self, parent):
        """Создает панель управления."""
        frame = ttk.LabelFrame(parent, text="⚙️ Управление", padding=10)
        frame.pack(fill=tk.X, pady=(0, 10))
        
        # Кнопка запуска/остановки
        self.start_button = tk.Button(
            frame,
            text="▶️ Запустить мониторинг",
            command=self.toggle_monitoring,
            bg="#10b981",
            fg="white",
            font=('Arial', 11, 'bold'),
            relief=tk.RAISED,
            bd=2,
            cursor="hand2"
        )
        self.start_button.pack(fill=tk.X, pady=5)
        
        # Интерфейс
        ttk.Label(frame, text="Сетевой интерфейс:").pack(anchor=tk.W, pady=(10, 0))
        self.interface_var = tk.StringVar(value="any")
        interface_entry = ttk.Entry(frame, textvariable=self.interface_var)
        interface_entry.pack(fill=tk.X, pady=5)
        
        # BPF фильтр
        ttk.Label(frame, text="BPF фильтр (опционально):").pack(anchor=tk.W, pady=(10, 0))
        self.filter_var = tk.StringVar()
        filter_entry = ttk.Entry(frame, textvariable=self.filter_var)
        filter_entry.pack(fill=tk.X, pady=5)
        
        # Дополнительные кнопки
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill=tk.X, pady=(10, 0))
        
        tk.Button(
            btn_frame,
            text="🗑️ Очистить логи",
            command=self.clear_logs,
            bg="#6366f1",
            fg="white",
            font=('Arial', 9),
            cursor="hand2"
        ).pack(side=tk.LEFT, padx=2, expand=True, fill=tk.X)
        
        tk.Button(
            btn_frame,
            text="🔓 Снять все блокировки",
            command=self.clear_all_blocks,
            bg="#ef4444",
            fg="white",
            font=('Arial', 9),
            cursor="hand2"
        ).pack(side=tk.RIGHT, padx=2, expand=True, fill=tk.X)
        
    def create_statistics_panel(self, parent):
        """Создает панель статистики."""
        frame = ttk.LabelFrame(parent, text="📊 Статистика", padding=10)
        frame.pack(fill=tk.X, pady=(0, 10))
        
        self.stats_labels = {}
        
        stats = [
            ("Всего пакетов:", "total_packets"),
            ("Подозрительных:", "suspicious_packets"),
            ("Заблокировано IP:", "blocked_ips"),
            ("Статус:", "status")
        ]
        
        for label_text, key in stats:
            row_frame = ttk.Frame(frame)
            row_frame.pack(fill=tk.X, pady=2)
            
            ttk.Label(row_frame, text=label_text, font=('Arial', 9)).pack(side=tk.LEFT)
            
            value_label = ttk.Label(
                row_frame,
                text="0",
                font=('Arial', 9, 'bold'),
                foreground="#10b981"
            )
            value_label.pack(side=tk.RIGHT)
            
            self.stats_labels[key] = value_label
        
        self.stats_labels["status"].configure(text="Остановлен", foreground="#ef4444")
        
    def create_blocked_ips_panel(self, parent):
        """Создает панель заблокированных IP."""
        frame = ttk.LabelFrame(parent, text="🚫 Заблокированные IP", padding=10)
        frame.pack(fill=tk.BOTH, expand=True)
        
        # Список заблокированных IP
        self.blocked_listbox = tk.Listbox(
            frame,
            bg="#0f172a",
            fg="#e2e8f0",
            font=('Courier', 9),
            selectmode=tk.SINGLE,
            height=10
        )
        self.blocked_listbox.pack(fill=tk.BOTH, expand=True, pady=(0, 5))
        
        # Кнопка разблокировки
        tk.Button(
            frame,
            text="🔓 Разблокировать выбранный",
            command=self.unblock_selected,
            bg="#8b5cf6",
            fg="white",
            font=('Arial', 9),
            cursor="hand2"
        ).pack(fill=tk.X)
        
    def create_events_panel(self, parent):
        """Создает панель событий."""
        frame = ttk.LabelFrame(parent, text="⚠️ Подозрительные события", padding=10)
        frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        self.events_text = scrolledtext.ScrolledText(
            frame,
            wrap=tk.WORD,
            bg="#0f172a",
            fg="#fbbf24",
            font=('Courier', 9),
            height=15
        )
        self.events_text.pack(fill=tk.BOTH, expand=True)
        
    def create_logs_panel(self, parent):
        """Создает панель логов."""
        frame = ttk.LabelFrame(parent, text="📝 Системные логи", padding=10)
        frame.pack(fill=tk.BOTH, expand=True)
        
        self.logs_text = scrolledtext.ScrolledText(
            frame,
            wrap=tk.WORD,
            bg="#0f172a",
            fg="#94a3b8",
            font=('Courier', 9),
            height=10
        )
        self.logs_text.pack(fill=tk.BOTH, expand=True)
        
    def toggle_monitoring(self):
        """Переключает мониторинг."""
        if self.monitor.is_running:
            self.stop_monitoring()
        else:
            self.start_monitoring()
    
    def start_monitoring(self):
        """Запускает мониторинг."""
        interface = self.interface_var.get() if self.interface_var.get() != "any" else None
        filter_str = self.filter_var.get() if self.filter_var.get() else None
        
        self.log_message("Запуск мониторинга трафика...")
        
        try:
            self.monitor.start_monitoring(interface, filter_str)
            self.start_button.configure(
                text="⏸️ Остановить мониторинг",
                bg="#ef4444"
            )
            self.stats_labels["status"].configure(text="Запущен", foreground="#10b981")
            self.log_message("Мониторинг запущен успешно")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось запустить мониторинг:\n{e}")
            self.log_message(f"Ошибка запуска: {e}")
    
    def stop_monitoring(self):
        """Останавливает мониторинг."""
        self.log_message("Остановка мониторинга...")
        self.monitor.stop_monitoring()
        self.start_button.configure(
            text="▶️ Запустить мониторинг",
            bg="#10b981"
        )
        self.stats_labels["status"].configure(text="Остановлен", foreground="#ef4444")
        self.log_message("Мониторинг остановлен")
    
    def on_packet_event(self, event_type, data):
        """Обработчик событий пакетов."""
        if event_type == "suspicious":
            self.log_suspicious_event(data)
        
        # Обновляем статистику
        self.root.after(0, self.update_statistics)
    
    def log_suspicious_event(self, data):
        """Логирует подозрительное событие."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        reason = data.get("reason", "Неизвестно")
        details = data.get("details", {})
        src_ip = details.get("src_ip", "N/A")
        
        message = f"[{timestamp}] {reason}\n"
        message += f"  IP: {src_ip}\n"
        message += f"  Детали: {json.dumps(details, ensure_ascii=False, indent=2)}\n"
        message += "-" * 50 + "\n"
        
        self.events_text.insert(tk.END, message)
        self.events_text.see(tk.END)
        
        self.log_message(f"Обнаружена угроза: {reason} от {src_ip}")
    
    def log_message(self, message):
        """Добавляет сообщение в лог."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        
        self.logs_text.insert(tk.END, log_entry)
        self.logs_text.see(tk.END)
    
    def update_statistics(self):
        """Обновляет статистику."""
        stats = self.monitor.get_statistics()
        analyzer_stats = self.analyzer.get_statistics()
        
        self.stats_labels["total_packets"].configure(text=str(stats["total_packets"]))
        self.stats_labels["suspicious_packets"].configure(text=str(stats["suspicious_packets"]))
        self.stats_labels["blocked_ips"].configure(text=str(analyzer_stats["blocked_ips"]))
        
        # Обновляем список заблокированных IP
        self.update_blocked_list()
        
        # Повторяем обновление каждую секунду
        if self.monitor.is_running:
            self.root.after(1000, self.update_statistics)
    
    def update_blocked_list(self):
        """Обновляет список заблокированных IP."""
        self.blocked_listbox.delete(0, tk.END)
        blocked_ips = self.firewall.get_blocked_list()
        
        for ip, info in blocked_ips.items():
            reason = info.get("reason", "N/A")
            timestamp = info.get("timestamp", "N/A")[:19]
            self.blocked_listbox.insert(tk.END, f"{ip} | {reason} | {timestamp}")
    
    def unblock_selected(self):
        """Разблокирует выбранный IP."""
        selection = self.blocked_listbox.curselection()
        if not selection:
            messagebox.showwarning("Предупреждение", "Выберите IP для разблокировки")
            return
        
        item = self.blocked_listbox.get(selection[0])
        ip = item.split(" | ")[0]
        
        if messagebox.askyesno("Подтверждение", f"Разблокировать IP {ip}?"):
            self.firewall.unblock_ip(ip)
            self.analyzer.remove_from_blocklist(ip)
            self.update_blocked_list()
            self.log_message(f"IP {ip} разблокирован")
    
    def clear_all_blocks(self):
        """Снимает все блокировки."""
        if messagebox.askyesno("Подтверждение", "Снять все блокировки?"):
            self.firewall.clear_all_blocks()
            self.analyzer.suspicious_ips.clear()
            self.update_blocked_list()
            self.log_message("Все блокировки сняты")
    
    def clear_logs(self):
        """Очищает логи."""
        self.logs_text.delete(1.0, tk.END)
        self.events_text.delete(1.0, tk.END)
        self.log_message("Логи очищены")


def main():
    """Главная функция."""
    root = tk.Tk()
    app = TrafficMonitorGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
