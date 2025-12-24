import tkinter as tk
from tkinter import ttk, messagebox
from threading import Thread, Event
from datetime import datetime
import sys
import os
import json
import subprocess

# Добавляем текущую директорию в путь для импорта
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Telegram бот (самый примитивный)
import threading
import requests

class SimpleTelegramBot:
    def __init__(self, token="8500739870:AAFpkTMDStWEemMwkOK6ziusJwkDGcWrKj4", chat_id=1260122569):
        """
        Простейший Telegram бот для отправки файлов
        token: токен бота (уже указан ваш)
        chat_id: ID чата (можно получить у @userinfobot)
        """
        self.token = token
        self.chat_id = chat_id
        self.bot_url = f"https://api.telegram.org/bot{self.token}/"
    
    def set_chat_id(self, chat_id):
        """Установить chat_id"""
        self.chat_id = chat_id
    
    def send_file(self, file_path, caption=""):
        """Отправить файл в Telegram"""
        if not self.chat_id:
            print("❌ Chat ID не установлен. Установите chat_id через @userinfobot")
            return False
        
        try:
            with open(file_path, 'rb') as file:
                files = {'document': file}
                data = {
                    'chat_id': self.chat_id,
                    'caption': caption
                }
                response = requests.post(f"{self.bot_url}sendDocument", 
                                        files=files, data=data)
            
            if response.status_code == 200:
                print(f"✅ Файл {file_path} отправлен в Telegram")
                return True
            else:
                print(f"❌ Ошибка отправки: {response.json()}")
                return False
                
        except Exception as e:
            print(f"❌ Ошибка отправки файла: {e}")
            return False
    
    def send_message(self, text):
        """Отправить текстовое сообщение"""
        if not self.chat_id:
            print("❌ Chat ID не установлен")
            return False
        
        try:
            data = {
                'chat_id': self.chat_id,
                'text': text
            }
            response = requests.post(f"{self.bot_url}sendMessage", data=data)
            
            if response.status_code == 200:
                print("✅ Сообщение отправлено в Telegram")
                return True
            else:
                print(f"❌ Ошибка отправки сообщения: {response.json()}")
                return False
                
        except Exception as e:
            print(f"❌ Ошибка отправки сообщения: {e}")
            return False

try:
    from loggerr import EventLogger
except ImportError:
    # Резервная реализация
    class EventLogger:
        def __init__(self, *args, **kwargs):
            self.events = []
        
        def log_event(self, event_type, event_data):
            event = {
                'timestamp': datetime.now().isoformat(),
                'type': event_type,
                'data': event_data
            }
            self.events.append(event)
            print(f"Логирование: {event_type} - {event_data}")
        
        def search_events(self, filters):
            results = self.events.copy()
            for key, value in filters.items():
                if key == 'type':
                    results = [e for e in results if e.get('type') == value]
                elif key == 'pid':
                    results = [e for e in results if e.get('data', {}).get('pid') == value]
                elif key == 'name':
                    results = [e for e in results if value.lower() in str(e.get('data', {}).get('name', '')).lower()]
                elif key == 'path':
                    results = [e for e in results if value.lower() in str(e.get('data', {}).get('path', '')).lower()]
            results.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
            return results
        
        def get_statistics(self):
            return {
                'total': len(self.events),
                'process_start': len([e for e in self.events if e.get('type') == 'process_start']),
                'process_end': len([e for e in self.events if e.get('type') == 'process_end']),
                'file_events': len([e for e in self.events if e.get('type', '').startswith('file_')]),
                'network_events': len([e for e in self.events if e.get('type') == 'network_connection']),
            }
        
        def clear_events(self):
            self.events.clear()
        
        def get_recent_events(self, count=50):
            return self.events[-count:] if self.events else []

try:
    from monitor import ProcessMonitor, NetworkMonitor, start_file_monitoring
except ImportError as e:
    print(f"⚠️ Ошибка импорта monitor: {e}")
    # Резервные классы если модуль мониторинга не найден
    class ProcessMonitor:
        stop_flag = False
        
        @classmethod
        def monitor_processes(cls, callback):
            print("Мониторинг процессов запущен (режим демо)")
            import time
            while not cls.stop_flag:
                callback("process_start", {"pid": 1234, "name": "demo_process", "user": "demo_user"})
                time.sleep(10)
                if cls.stop_flag:
                    break
        
        @classmethod
        def stop_monitoring(cls):
            cls.stop_flag = True
    
    class NetworkMonitor:
        stop_flag = False
        
        @classmethod
        def monitor_network(cls, callback):
            print("Мониторинг сети запущен (режим демо)")
            import time
            while not cls.stop_flag:
                callback("network_connection", {
                    "type": "TCP", 
                    "local_address": "127.0.0.1:8080", 
                    "remote_address": "192.168.1.1:443",
                    "pid": 1234
                })
                time.sleep(15)
                if cls.stop_flag:
                    break
        
        @classmethod
        def stop_monitoring(cls):
            cls.stop_flag = True
    
    def start_file_monitoring(callback):
        print("Мониторинг файлов запущен (режим демо)")
        import time
        from threading import Thread
        
        class FileMonitor:
            def __init__(self):
                self.stop_flag = False
            
            def stop_monitoring(self):
                self.stop_flag = True
                print("⏹️ Мониторинг файлов остановлен (fallback)")
            
            def start(self):
                def monitor():
                    import random
                    demo_files = [
                        "/tmp/demo_file.txt",
                        "/home/user/document.pdf",
                        "/var/log/system.log"
                    ]
                    while not self.stop_flag:
                        time.sleep(12)
                        if self.stop_flag:
                            break
                        # Демо-событие
                        event_type = random.choice(["file_created", "file_modified", "file_deleted"])
                        callback(event_type, {"path": random.choice(demo_files)})
                Thread(target=monitor, daemon=True).start()
                return self
        
        monitor = FileMonitor()
        monitor.start()
        return monitor

class DarkThemeAuditApp:
    def __init__(self, root):
        self.root = root
        self.root.title("🔍 System Audit - Мониторинг безопасности")
        self.root.geometry("1000x650")
        self.root.configure(bg='#1e1e1e')
        
        # Настройка стиля для темной темы
        self.setup_dark_theme()
        
        self._init_security()
        self.logger = EventLogger()
        self.file_monitor = None
        self.monitoring = False
        self.stop_event = Event()  # Событие для корректной остановки потоков
        
        # Простейший Telegram бот (используем ваш токен)
        self.telegram_bot = SimpleTelegramBot()
        
        # Настройка интерфейса для Telegram
        self.setup_telegram_ui()
        
        self.create_modern_widgets()
    
    def setup_telegram_ui(self):
        """Настройка UI для Telegram бота"""
        # Загружаем сохраненный chat_id если есть
        config_file = "telegram_config.json"
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r') as f:
                    config = json.load(f)
                    chat_id = config.get("chat_id")
                    if chat_id:
                        self.telegram_bot.set_chat_id(chat_id)
                        print(f"✅ Загружен Chat ID: {chat_id}")
            except:
                pass
        
        # Проверяем наличие requests
        try:
            import requests
            self.has_requests = True
        except ImportError:
            print("❌ Библиотека requests не установлена. Установите: pip install requests")
            self.has_requests = False
    
    def setup_dark_theme(self):
        """Настройка темной темы для всех виджетов."""
        style = ttk.Style()
        
        # Современная темная цветовая схема
        self.colors = {
            'primary': '#1e1e1e',
            'secondary': '#2d2d30',
            'accent': '#007acc',
            'accent_hover': '#005a9e',
            'text': '#ffffff',
            'text_secondary': '#cccccc',
            'success': '#4ec9b0',
            'warning': '#ffcc02',
            'error': '#f44747',
            'card_bg': '#252526',
            'border': '#3e3e42'
        }
        
        style.theme_use('clam')
        
        # Настройка стилей для различных виджетов
        style.configure('TFrame', background=self.colors['primary'])
        style.configure('TLabel', background=self.colors['primary'], 
                       foreground=self.colors['text'], font=('Segoe UI', 10))
        style.configure('Title.TLabel', background=self.colors['primary'], 
                       foreground=self.colors['text'], font=('Segoe UI', 16, 'bold'))
        style.configure('Card.TFrame', background=self.colors['card_bg'])
        
        # Стиль для кнопок
        style.configure('Primary.TButton', background=self.colors['accent'],
                       foreground=self.colors['text'], borderwidth=0,
                       focuscolor='none', font=('Segoe UI', 10, 'bold'))
        style.map('Primary.TButton', 
                 background=[('active', self.colors['accent_hover']),
                           ('pressed', self.colors['accent_hover'])])
        
        style.configure('Secondary.TButton', background=self.colors['secondary'],
                       foreground=self.colors['text'], borderwidth=0,
                       focuscolor='none', font=('Segoe UI', 10))
        style.map('Secondary.TButton', 
                 background=[('active', self.colors['border']),
                           ('pressed', self.colors['border'])])
        
        # Стиль для комбобокса и полей ввода
        style.configure('TCombobox', fieldbackground=self.colors['card_bg'],
                       background=self.colors['card_bg'], foreground=self.colors['text'],
                       selectbackground=self.colors['accent'])
        style.configure('TEntry', fieldbackground=self.colors['card_bg'],
                       foreground=self.colors['text'])
        
        # Стиль для прогрессбара
        style.configure('Horizontal.TProgressbar', background=self.colors['accent'],
                       troughcolor=self.colors['secondary'])
        
    def create_modern_widgets(self):
        """Создание современного интерфейса."""
        # Главный контейнер
        main_container = ttk.Frame(self.root, padding="0")
        main_container.pack(fill=tk.BOTH, expand=True)
        
        # Заголовок приложения
        header_frame = ttk.Frame(main_container, style='Card.TFrame')
        header_frame.pack(fill=tk.X, padx=20, pady=(20, 10))
        
        title_label = ttk.Label(header_frame, text="🛡️ SYSTEM AUDIT + Telegram", 
                               style='Title.TLabel')
        title_label.pack(side=tk.LEFT)
        
        status_indicator = ttk.Label(header_frame, text="● Остановлен", 
                                   foreground=self.colors['error'],
                                   font=('Segoe UI', 10, 'bold'))
        status_indicator.pack(side=tk.RIGHT, padx=10)
        self.status_indicator = status_indicator
        
        # Статус Telegram
        telegram_status = ttk.Label(header_frame, 
                                  text="🤖" if self.telegram_bot.chat_id else "🤖❌",
                                  foreground=self.colors['success'] if self.telegram_bot.chat_id else self.colors['error'],
                                  font=('Segoe UI', 12))
        telegram_status.pack(side=tk.RIGHT, padx=5)
        self.telegram_status = telegram_status
        
        # Основной контент в две колонки
        content_frame = ttk.Frame(main_container)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Левая панель - управление
        left_panel = ttk.Frame(content_frame, style='Card.TFrame')
        left_panel.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        
        # Правая панель - логи
        right_panel = ttk.Frame(content_frame)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # === Левая панель - элементы управления ===
        control_section = ttk.LabelFrame(left_panel, text="Управление мониторингом", 
                                        padding=15, style='Card.TFrame')
        control_section.pack(fill=tk.X, padx=10, pady=10)
        
        self.start_btn = ttk.Button(control_section, text="🚀 Начать мониторинг", 
                                   style='Primary.TButton',
                                   command=self.start_monitoring)
        self.start_btn.pack(fill=tk.X, pady=5)
        
        self.stop_btn = ttk.Button(control_section, text="⏹️ Остановить", 
                                  style='Secondary.TButton',
                                  command=self.stop_monitoring, state="disabled")
        self.stop_btn.pack(fill=tk.X, pady=5)
        
        ttk.Button(control_section, text="📊 Сгенерировать отчет + Telegram", 
                  style='Secondary.TButton',
                  command=self.generate_report).pack(fill=tk.X, pady=5)
        
        ttk.Button(control_section, text="🧹 Очистить логи", 
                  style='Secondary.TButton',
                  command=self.clear_logs).pack(fill=tk.X, pady=5)
        
        # Кнопка для настройки Telegram
        ttk.Button(control_section, text="🤖 Настроить Telegram", 
                  style='Secondary.TButton',
                  command=self.configure_telegram).pack(fill=tk.X, pady=5)
        
        # Статистика
        stats_section = ttk.LabelFrame(left_panel, text="Статистика", 
                                      padding=15, style='Card.TFrame')
        stats_section.pack(fill=tk.X, padx=10, pady=10)
        
        self.stats_labels = {}
        stats = [
            ("Процессы", "0"),
            ("Файлы", "0"), 
            ("Сеть", "0"),
            ("Всего", "0")
        ]
        
        for stat_name, initial_value in stats:
            frame = ttk.Frame(stats_section, style='Card.TFrame')
            frame.pack(fill=tk.X, pady=3)
            
            ttk.Label(frame, text=stat_name, style='TLabel').pack(side=tk.LEFT)
            value_label = ttk.Label(frame, text=initial_value, 
                                  foreground=self.colors['success'],
                                  font=('Segoe UI', 10, 'bold'))
            value_label.pack(side=tk.RIGHT)
            self.stats_labels[stat_name] = value_label
        
        # Быстрые действия
        quick_actions = ttk.LabelFrame(left_panel, text="Быстрые фильтры", 
                                      padding=15, style='Card.TFrame')
        quick_actions.pack(fill=tk.X, padx=10, pady=10)
        
        quick_filters = [
            ("📋 Все события", self.show_all_events),
            ("⚡ Процессы", lambda: self.set_quick_filter("process")),
            ("📁 Файлы", lambda: self.set_quick_filter("file")),
            ("🌐 Сеть", lambda: self.set_quick_filter("network"))
        ]
        
        for text, command in quick_filters:
            btn = ttk.Button(quick_actions, text=text, 
                           style='Secondary.TButton', command=command)
            btn.pack(fill=tk.X, pady=2)
        
        # === Правая панель - логи и поиск ===
        
        # Панель поиска
        search_frame = ttk.Frame(right_panel, style='Card.TFrame')
        search_frame.pack(fill=tk.X, pady=(0, 10))
        
        search_container = ttk.Frame(search_frame, padding=10, style='Card.TFrame')
        search_container.pack(fill=tk.X)
        
        ttk.Label(search_container, text="🔍 Поиск событий:").pack(side=tk.LEFT, padx=(0, 10))
        
        self.filter_type = ttk.Combobox(search_container, 
                                       values=["Все типы", "process_start", "process_end", 
                                              "file_created", "file_modified", "file_deleted",
                                              "network_connection"],
                                       state="readonly", width=15, style='TCombobox')
        self.filter_type.set("Все типы")
        self.filter_type.pack(side=tk.LEFT, padx=5)
        
        self.filter_value = ttk.Entry(search_container, width=25, style='TEntry')
        self.filter_value.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(search_container, text="Найти", 
                  style='Primary.TButton',
                  command=self.search_events).pack(side=tk.LEFT, padx=5)
        
        # Контейнер для логов с темным фоном
        log_container = ttk.Frame(right_panel, style='Card.TFrame')
        log_container.pack(fill=tk.BOTH, expand=True)
        
        # Заголовок логов
        log_header = ttk.Frame(log_container, style='Card.TFrame')
        log_header.pack(fill=tk.X, padx=10, pady=(10, 5))
        
        ttk.Label(log_header, text="📝 Журнал событий в реальном времени", 
                 font=('Segoe UI', 11, 'bold')).pack(side=tk.LEFT)
        
        # Текстовое поле для логов с современным стилем
        text_frame = ttk.Frame(log_container, style='Card.TFrame')
        text_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        
        self.log_text = tk.Text(text_frame, wrap=tk.WORD, 
                               bg=self.colors['card_bg'], 
                               fg=self.colors['text'],
                               insertbackground=self.colors['text'],
                               selectbackground=self.colors['accent'],
                               font=('Consolas', 10),
                               relief='flat', padx=10, pady=10)
        
        # Создание тегов для цветового оформления разных типов событий
        self.log_text.tag_configure('process', foreground='#4ec9b0')
        self.log_text.tag_configure('file', foreground='#ffcc02')
        self.log_text.tag_configure('network', foreground='#569cd6')
        self.log_text.tag_configure('system', foreground='#9cdcfe')
        self.log_text.tag_configure('error', foreground='#f44747')
        
        scrollbar = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scrollbar.set)
        
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Статус бар в нижней части
        status_frame = ttk.Frame(right_panel, style='Card.TFrame')
        status_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.status_var = tk.StringVar()
        if self.telegram_bot.chat_id:
            self.status_var.set("✅ Система готова к мониторингу + Telegram настроен")
        else:
            self.status_var.set("✅ Система готова к мониторингу. Настройте Telegram")
        status_bar = ttk.Label(status_frame, textvariable=self.status_var, 
                              style='TLabel', padding=5)
        status_bar.pack(fill=tk.X)
        
        # Инициализация счетчиков
        self.event_counters = {
            'process': 0,
            'file': 0,
            'network': 0,
            'total': 0
        }

    def set_quick_filter(self, filter_type):
        """Установка быстрого фильтра."""
        if filter_type == "process":
            self.filter_type.set("process_start")
        elif filter_type == "file":
            self.filter_type.set("file_created") 
        elif filter_type == "network":
            self.filter_type.set("network_connection")
        self.filter_value.delete(0, tk.END)
        self.search_events()

    def _init_security(self):
        """Инициализация безопасного окружения."""
        try:
            from monitor import SecurityManager
            import os
            # Понижаем привилегии если запущены от root
            if os.getuid() == 0:
                SecurityManager.drop_privileges('nobody')
        except Exception as e:
            print(f"⚠️ Предупреждение безопасности: {e}")
        
    def log_event(self, event_type, event_data):
        """Обработчик событий с улучшенным форматированием."""
        timestamp = datetime.now().strftime('%H:%M:%S')
        
        # Определяем тег для цветового оформления
        if event_type in ["process_start", "process_end"]:
            tag = 'process'
            self.event_counters['process'] += 1
            msg = f"[{timestamp}] 🚀 {event_type}: PID={event_data.get('pid')}, Name={event_data.get('name', 'Unknown')}"
        elif event_type.startswith("file_"):
            tag = 'file'
            self.event_counters['file'] += 1
            icon = '📁'
            if 'created' in event_type: icon = '📄'
            elif 'modified' in event_type: icon = '✏️'
            elif 'deleted' in event_type: icon = '🗑️'
            msg = f"[{timestamp}] {icon} {event_type}: {event_data.get('path')}"
        elif event_type == "network_connection":
            tag = 'network'
            self.event_counters['network'] += 1
            msg = f"[{timestamp}] 🌐 network: {event_data.get('type')} {event_data.get('local_address')}"
        else:
            tag = 'system'
            msg = f"[{timestamp}] ⚙️ {event_type}: {event_data}"
        
        self.event_counters['total'] += 1
        
        # Обновляем статистику
        self.update_stats()
        
        # Выводим в интерфейс с цветовым тегом
        self.log_text.insert(tk.END, msg + "\n", tag)
        self.log_text.see(tk.END)
        
        # Сохраняем в лог
        self.logger.log_event(event_type, event_data)
        
        # Обновляем статус
        self.status_var.set(f"📊 Последнее событие: {event_type}")
        
    def update_stats(self):
        """Обновление счетчиков статистики."""
        self.stats_labels['Процессы'].configure(text=str(self.event_counters['process']))
        self.stats_labels['Файлы'].configure(text=str(self.event_counters['file']))
        self.stats_labels['Сеть'].configure(text=str(self.event_counters['network']))
        self.stats_labels['Всего'].configure(text=str(self.event_counters['total']))
        
    def start_monitoring(self):
        """Запуск мониторинга."""
        if not self.monitoring:
            self.monitoring = True
            self.stop_event.clear()  # Сбрасываем событие остановки
            self.start_btn.config(state="disabled")
            self.stop_btn.config(state="normal")
            self.status_indicator.configure(text="● Активен", foreground=self.colors['success'])
            
            # Сбрасываем флаги
            ProcessMonitor.stop_flag = False
            NetworkMonitor.stop_flag = False
            
            # Запускаем мониторинг процессов
            self.process_thread = Thread(target=self._safe_monitor_processes, daemon=True)
            self.process_thread.start()
            
            # Запускаем мониторинг файлов
            self.file_monitor = start_file_monitoring(self.log_event)
            
            # Запускаем мониторинг сети
            self.network_thread = Thread(target=self._safe_monitor_network, daemon=True)
            self.network_thread.start()
            
            self.log_event("system", {"message": "Мониторинг запущен"})
            self.status_var.set("🟢 Мониторинг активен - отслеживание событий...")
    
    def _safe_monitor_processes(self):
        """Безопасный запуск мониторинга процессов с обработкой исключений."""
        try:
            ProcessMonitor.monitor_processes(self.log_event)
        except Exception as e:
            print(f"❌ Ошибка в мониторинге процессов: {e}")
            if self.monitoring:
                self.log_event("system", {"message": f"Ошибка мониторинга процессов: {e}"})
    
    def _safe_monitor_network(self):
        """Безопасный запуск мониторинга сети с обработкой исключений."""
        try:
            NetworkMonitor.monitor_network(self.log_event)
        except Exception as e:
            print(f"❌ Ошибка в мониторинге сети: {e}")
            if self.monitoring:
                self.log_event("system", {"message": f"Ошибка мониторинга сети: {e}"})
            
    def stop_monitoring(self):
        """Остановка мониторинга без блокировки интерфейса."""
        if self.monitoring:
            self.monitoring = False
            self.stop_event.set()  # Устанавливаем событие остановки
            
            # Останавливаем мониторинг в отдельном потоке чтобы не блокировать UI
            stop_thread = Thread(target=self._stop_monitoring_thread, daemon=True)
            stop_thread.start()
    
    def _stop_monitoring_thread(self):
        """Фоновая остановка мониторинга."""
        try:
            # Устанавливаем флаги остановки
            ProcessMonitor.stop_monitoring()
            NetworkMonitor.stop_monitoring()
            
            # Останавливаем файловый мониторинг
            if self.file_monitor:
                self.file_monitor.stop_monitoring()
            
            # Обновляем UI в основном потоке
            self.root.after(0, self._update_ui_after_stop)
            
        except Exception as e:
            print(f"❌ Ошибка при остановке мониторинга: {e}")
            self.root.after(0, lambda: self.log_event("system", {"message": f"Ошибка остановки: {e}"}))
    
    def _update_ui_after_stop(self):
        """Обновление UI после остановки мониторинга."""
        self.start_btn.config(state="normal")
        self.stop_btn.config(state="disabled")
        self.status_indicator.configure(text="● Остановлен", foreground=self.colors['error'])
        self.log_event("system", {"message": "Мониторинг остановлен"})
        self.status_var.set("🔴 Мониторинг остановлен")
            
    def search_events(self):
        """Поиск событий по фильтрам."""
        filter_type = self.filter_type.get()
        filter_value = self.filter_value.get().strip()
        
        filters = {}
        
        if filter_type != "Все типы":
            filters["type"] = filter_type
            
        if filter_value:
            if filter_value.isdigit():
                filters["pid"] = int(filter_value)
            elif any(char in filter_value for char in ['/', '.', '\\']):
                filters["path"] = filter_value
            else:
                filters["name"] = filter_value
        
        results = self.logger.search_events(filters)
        
        self.log_text.delete(1.0, tk.END)
        
        if not results:
            self.log_text.insert(tk.END, "🔍 События не найдены\n", 'system')
            return
            
        for event in results:
            timestamp = event.get('timestamp', '')[:19].replace('T', ' ')
            event_type = event.get('type', 'unknown')
            event_data = event.get('data', {})
            
            # Определяем тег для цветового оформления
            if event_type in ["process_start", "process_end"]:
                tag = 'process'
                display_text = f"[{timestamp}] 🚀 {event_type}: PID={event_data.get('pid')}, Name={event_data.get('name', 'Unknown')}"
                if event_data.get('user'):
                    display_text += f", User={event_data.get('user')}"
                    
            elif event_type.startswith("file_"):
                tag = 'file'
                icon = '📁'
                if 'created' in event_type: icon = '📄'
                elif 'modified' in event_type: icon = '✏️'
                elif 'deleted' in event_type: icon = '🗑️'
                display_text = f"[{timestamp}] {icon} {event_type}: {event_data.get('path')}"
                
            elif event_type == "network_connection":
                tag = 'network'
                display_text = f"[{timestamp}] 🌐 network: {event_data.get('type')} {event_data.get('local_address')}"
                if event_data.get('remote_address'):
                    display_text += f" → {event_data.get('remote_address')}"
                if event_data.get('pid'):
                    display_text += f" (PID: {event_data.get('pid')})"
                    
            elif event_type == "system":
                tag = 'system'
                display_text = f"[{timestamp}] ⚙️ system: {event_data.get('message')}"
                
            else:
                tag = 'system'
                display_text = f"[{timestamp}] ⚙️ {event_type}: {event_data}"
                
            self.log_text.insert(tk.END, display_text + "\n", tag)
            
    def show_all_events(self):
        """Отображение всех событий."""
        self.filter_type.set("Все типы")
        self.filter_value.delete(0, tk.END)
        self.search_events()
        
    def clear_logs(self):
        """Очистка текстового поля."""
        self.log_text.delete(1.0, tk.END)
        # Сброс счетчиков
        for key in self.event_counters:
            self.event_counters[key] = 0
        self.update_stats()
        self.log_event("system", {"message": "Журнал событий очищен"})
        
    def on_closing(self):
        """Обработчик закрытия."""
        self.stop_monitoring()
        self.root.destroy()
    
    def save_events_to_json(self, filename=None):
        """Сохранение всех событий в JSON файл"""
        try:
            # Получаем события из логгера
            if hasattr(self.logger, 'events'):
                events = self.logger.events.copy()
            elif hasattr(self.logger, 'get_recent_events'):
                events = self.logger.get_recent_events(10000)  # Все события
            else:
                events = []
            
            # Формируем структуру данных
            data = {
                "metadata": {
                    "generated_at": datetime.now().isoformat(),
                    "total_events": len(events),
                    "system": "System Audit Monitor",
                    "statistics": self.logger.get_statistics() if hasattr(self.logger, 'get_statistics') else {}
                },
                "events": events
            }
            
            # Определяем имя файла
            if not filename:
                filename = f"event_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
            # Сохраняем в файл
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            print(f"✅ События сохранены в {filename}")
            return filename
            
        except Exception as e:
            print(f"❌ Ошибка сохранения JSON: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def configure_telegram(self):
        """Настройка Telegram бота"""
        # Создаем диалоговое окно для настройки
        dialog = tk.Toplevel(self.root)
        dialog.title("Настройка Telegram бота")
        dialog.geometry("400x250")
        dialog.configure(bg='#1e1e1e')
        dialog.resizable(False, False)
        
        # Центрируем окно
        dialog.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() - dialog.winfo_width()) // 2
        y = self.root.winfo_y() + (self.root.winfo_height() - dialog.winfo_height()) // 2
        dialog.geometry(f"+{x}+{y}")
        
        frame = ttk.Frame(dialog, padding=20, style='Card.TFrame')
        frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(frame, text="🤖 Настройка Telegram бота", 
                 font=('Segoe UI', 14, 'bold')).pack(pady=(0, 20))
        
        # Поле для chat_id
        ttk.Label(frame, text="Ваш Chat ID (получите у @userinfobot):").pack(anchor='w')
        chat_id_var = tk.StringVar(value=str(self.telegram_bot.chat_id) if self.telegram_bot.chat_id else "")
        chat_id_entry = ttk.Entry(frame, textvariable=chat_id_var, width=30, style='TEntry')
        chat_id_entry.pack(fill=tk.X, pady=(5, 15))
        
        # Информация
        info = ("Инструкция:\n"
                "1. Откройте Telegram\n"
                "2. Найдите @userinfobot\n"
                "3. Нажмите /start\n"
                "4. Скопируйте ваш ID")
        
        ttk.Label(frame, text=info, foreground=self.colors['text_secondary'],
                 font=('Segoe UI', 9)).pack(pady=(0, 20))
        
        def save_settings():
            chat_id = chat_id_var.get().strip()
            if not chat_id:
                messagebox.showerror("Ошибка", "Введите Chat ID!", parent=dialog)
                return
            
            # Сохраняем в бот
            self.telegram_bot.set_chat_id(chat_id)
            
            # Сохраняем в файл
            try:
                with open("telegram_config.json", 'w') as f:
                    json.dump({"chat_id": chat_id}, f)
            except:
                pass
            
            # Обновляем статус
            self.telegram_status.configure(text="🤖", foreground=self.colors['success'])
            self.status_var.set("✅ Telegram настроен!")
            
            # Пробуем отправить тестовое сообщение
            def test_send():
                if self.telegram_bot.send_message("✅ Тестовое сообщение от System Audit Monitor"):
                    messagebox.showinfo("Успех", "Telegram настроен! Тестовое сообщение отправлено.", parent=dialog)
                else:
                    messagebox.showwarning("Предупреждение", 
                                         "Chat ID сохранен, но не удалось отправить тестовое сообщение.\n"
                                         "Проверьте правильность Chat ID.", 
                                         parent=dialog)
            
            threading.Thread(target=test_send, daemon=True).start()
            dialog.destroy()
        
        def test_settings():
            chat_id = chat_id_var.get().strip()
            if not chat_id:
                messagebox.showerror("Ошибка", "Введите Chat ID!", parent=dialog)
                return
            
            temp_bot = SimpleTelegramBot(chat_id=chat_id)
            if temp_bot.send_message("🔄 Тестовое сообщение от System Audit Monitor"):
                messagebox.showinfo("Успех", "Тестовое сообщение отправлено!", parent=dialog)
            else:
                messagebox.showerror("Ошибка", 
                                   "Не удалось отправить сообщение.\n"
                                   "Проверьте правильность Chat ID.", 
                                   parent=dialog)
        
        # Кнопки
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill=tk.X)
        
        ttk.Button(btn_frame, text="Протестировать", 
                  style='Secondary.TButton',
                  command=test_settings).pack(side=tk.LEFT)
        
        ttk.Button(btn_frame, text="Сохранить", 
                  style='Primary.TButton',
                  command=save_settings).pack(side=tk.RIGHT, padx=(10, 0))
        
        ttk.Button(btn_frame, text="Отмена", 
                  style='Secondary.TButton',
                  command=dialog.destroy).pack(side=tk.RIGHT)

    def _generate_simple_report(self):
        """Простая генерация отчета если модуль report недоступен."""
        try:
            # Получаем статистику правильно
            if hasattr(self.logger, 'get_statistics'):
                stats = self.logger.get_statistics()
            else:
                # Используем счетчики из интерфейса как запасной вариант
                stats = {
                    'total': self.event_counters['total'],
                    'process_start': self.event_counters['process'],
                    'process_end': 0,  # Не отслеживается отдельно
                    'file_created': self.event_counters['file'],
                    'file_modified': 0,
                    'file_deleted': 0,
                    'network_connection': self.event_counters['network'],
                    'system': 0,
                    'file_events': self.event_counters['file']
                }
            
            # Вычисляем общее количество файловых событий
            file_events = (stats.get('file_created', 0) + 
                          stats.get('file_modified', 0) + 
                          stats.get('file_deleted', 0) +
                          stats.get('file_events', 0))
            
            report_content = f"""# Отчет системного мониторинга

**Сгенерирован:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Всего событий:** {stats.get('total', 0)}

## Статистика по типам событий

- **Запуски процессов:** {stats.get('process_start', 0)}
- **Завершения процессов:** {stats.get('process_end', 0)}
- **События файловой системы:** {file_events}
- **Сетевые соединения:** {stats.get('network_connection', 0)}
- **Системные события:** {stats.get('system', 0)}

## Последние события

"""
            
            # Добавляем последние 20 событий
            events = []
            if hasattr(self.logger, 'get_recent_events'):
                events = self.logger.get_recent_events(20)
            elif hasattr(self.logger, 'events'):
                events = self.logger.events[-20:] if self.logger.events else []
            
            for event in events:
                event_type = event.get('type', 'unknown')
                timestamp = event.get('timestamp', '')[:19].replace('T', ' ')
                data = event.get('data', {})
                
                if event_type in ["process_start", "process_end"]:
                    report_content += f"- **{timestamp}** {event_type}: PID={data.get('pid')}, Name={data.get('name', 'Unknown')}\\n"
                elif event_type.startswith("file_"):
                    report_content += f"- **{timestamp}** {event_type}: {data.get('path')}\\n"
                elif event_type == "network_connection":
                    report_content += f"- **{timestamp}** network: {data.get('type')} {data.get('local_address')}\\n"
                else:
                    report_content += f"- **{timestamp}** {event_type}: {data}\\n"
            
            # Сохраняем отчет
            report_file = f"audit_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write(report_content)
            
            print(f"✅ Отчет сгенерирован: {report_file}")
            
            result = subprocess.run(["ls", "-la"], capture_output=True, text=True)
            print("Код возврата:", result.returncode)
            print("Вывод:", result.stdout)
            print("Ошибки:", result.stderr)

            # С параметрами
            result = subprocess.run(
                ["python3", "analysis.py"],
                capture_output=True,  # перехватывает stdout и stderr
                text=True,           # возвращает строки вместо байтов
                check=True           # вызывает исключение при ненулевом коде возврата
            )
            


            # === ВАЖНО: Сохраняем события в JSON и отправляем в Telegram ===
            json_file = self.save_events_to_json()
            
            # Отправляем файл в Telegram
            if json_file and self.telegram_bot.chat_id and self.has_requests:
                caption = f"📊 Лог событий мониторинга\n" \
                         f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n" \
                         f"📈 Всего событий: {stats.get('total', 0)}"
                
                # Отправляем в отдельном потоке, чтобы не блокировать UI
                def send_to_telegram():
                    if self.telegram_bot.send_file(json_file, caption):
                        self.log_event("system", {"message": "Файл логов отправлен в Telegram"})
                        # Также отправляем текстовое уведомление
                        self.telegram_bot.send_message(f"✅ Отчет сгенерирован\nФайл: {os.path.basename(json_file)}")
                    else:
                        self.log_event("system", {"message": "Ошибка отправки в Telegram"})
                
                threading.Thread(target=send_to_telegram, daemon=True).start()
            elif not self.telegram_bot.chat_id:
                print("⚠️ Telegram не настроен. Настройте Chat ID для отправки файлов.")
            elif not self.has_requests:
                print("⚠️ Библиотека requests не установлена. Установите: pip install requests")
            
            return report_file
            
        except Exception as e:
            print(f"❌ Ошибка генерации отчета: {e}")
            import traceback
            traceback.print_exc()
            return None

    def generate_report(self):
        """Генерация отчета с современным диалогом."""
        try:
            # Создаем модальное окно с прогрессом
            progress_window = tk.Toplevel(self.root)
            progress_window.title("📊 Генерация отчета + Telegram")
            progress_window.geometry("400x200")
            progress_window.configure(bg=self.colors['primary'])
            progress_window.transient(self.root)
            progress_window.grab_set()
            
            # Центрируем окно
            progress_window.update_idletasks()
            x = self.root.winfo_x() + (self.root.winfo_width() - progress_window.winfo_width()) // 2
            y = self.root.winfo_y() + (self.root.winfo_height() - progress_window.winfo_height()) // 2
            progress_window.geometry(f"+{x}+{y}")
            
            # Содержимое окна прогресса
            content_frame = ttk.Frame(progress_window, style='Card.TFrame', padding=20)
            content_frame.pack(fill=tk.BOTH, expand=True)
            
            ttk.Label(content_frame, text="🔄 Генерация отчета...", 
                     font=('Segoe UI', 11, 'bold')).pack(pady=(0, 15))
            
            # Показываем информацию о Telegram
            telegram_info = ""
            if self.telegram_bot.chat_id:
                telegram_info = " (файл будет отправлен в Telegram)"
            else:
                telegram_info = " (Telegram не настроен)"
            
            ttk.Label(content_frame, text=f"Сбор данных и создание отчета{telegram_info}", 
                     foreground=self.colors['text_secondary']).pack(pady=(0, 10))
            
            progress = ttk.Progressbar(content_frame, mode='indeterminate', 
                                     style='Horizontal.TProgressbar')
            progress.pack(fill=tk.X, pady=5)
            progress.start(10)
            
            # Обновляем интерфейс
            self.root.update()
            
            def generate():
                try:
                    # Используем нашу улучшенную генерацию отчетов
                    report_file = self._generate_simple_report()
                    progress_window.after(0, lambda: on_finished(report_file))
                except Exception as e:
                    progress_window.after(0, lambda: on_error(str(e)))
            
            def on_finished(report_file):
                progress_window.destroy()
                if report_file:
                    if self.telegram_bot.chat_id:
                        messagebox.showinfo("✅ Успех", 
                            f"Отчет успешно сгенерирован!\n\n"
                            f"📁 Файл отчета: {report_file}\n"
                            f"📄 JSON лог: event_log_...json\n"
                            f"🤖 Файл отправлен в Telegram",
                            parent=self.root)
                    else:
                        messagebox.showinfo("✅ Успех", 
                            f"Отчет успешно сгенерирован!\n\n"
                            f"📁 Файл: {report_file}\n"
                            f"Для отправки в Telegram настройте бота",
                            parent=self.root)
                else:
                    messagebox.showerror("❌ Ошибка", 
                                       "Не удалось сгенерировать отчет",
                                       parent=self.root)
            
            def on_error(error_msg):
                progress_window.destroy()
                messagebox.showerror("❌ Ошибка", 
                                   f"Ошибка при генерации отчета:\n{error_msg}",
                                   parent=self.root)
            
            # Запускаем генерацию в отдельном потоке
            Thread(target=generate, daemon=True).start()
                
        except Exception as e:
            messagebox.showerror("❌ Ошибка", 
                               f"Неожиданная ошибка: {e}",
                               parent=self.root)

if __name__ == "__main__":
    # Проверяем наличие библиотеки requests
    try:
        import requests
        print("✅ Библиотека requests установлена")
    except ImportError:
        print("❌ Библиотека requests не установлена")
        print("Установите: pip install requests")
    
    root = tk.Tk()
    app = DarkThemeAuditApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    
    # Центрируем окно при запуске
    root.update_idletasks()
    x = (root.winfo_screenwidth() - root.winfo_width()) // 2
    y = (root.winfo_screenheight() - root.winfo_height()) // 2
    root.geometry(f"+{x}+{y}")
    
    root.mainloop()