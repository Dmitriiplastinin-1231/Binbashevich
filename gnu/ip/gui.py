"""
Современный графический интерфейс для мониторинга сетевого трафика.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import logging
from datetime import datetime
import json
from collections import deque

from traffic_analyzer import TrafficAnalyzer
from firewall_manager import FirewallManager
from traffic_monitor import TrafficMonitor


class ModernTrafficMonitorGUI:
    """Современный графический интерфейс для мониторинга трафика."""
    
    def __init__(self, root):
        self.root = root
        self.root.title("🛡️ Network Guardian - Система защиты сети")
        self.root.geometry("1000x800")
        self.root.configure(bg="#0a0e27")
        
        # Инициализация компонентов
        self.analyzer = TrafficAnalyzer()
        self.firewall = FirewallManager()
        self.monitor = TrafficMonitor(
            self.analyzer,
            self.firewall,
            callback=self.on_packet_event
        )
        
        self.setup_logging()
        self.create_modern_interface()
        self.update_interface()
        
    def setup_logging(self):
        """Настройка логирования."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        
    def create_modern_interface(self):
        """Создает современный интерфейс."""
        
        # Настройка стилей
        self.setup_styles()
        
        # Верхняя панель - заголовок и статус
        self.create_header()
        
        # Главный контейнер с двумя колонками
        main_frame = tk.Frame(self.root, bg="#0a0e27")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)
        
        # Левая панель - контроль и статистика
        left_panel = tk.Frame(main_frame, bg="#0a0e27", width=480)
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, padx=(0, 10))
        left_panel.pack_propagate(False)
        
        self.create_control_cards(left_panel)
        
        # Правая панель - события и логи
        right_panel = tk.Frame(main_frame, bg="#0a0e27")
        right_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.create_events_panel(right_panel)
        
    def setup_styles(self):
        """Настройка современных стилей."""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Цвета
        self.colors = {
            'bg_dark': '#0a0e27',
            'bg_card': '#1a1f3a',
            'bg_card_hover': '#242947',
            'accent_blue': '#3b82f6',
            'accent_purple': '#8b5cf6',
            'accent_green': '#10b981',
            'accent_red': '#ef4444',
            'accent_yellow': '#f59e0b',
            'text_light': '#e2e8f0',
            'text_muted': '#94a3b8',
            'border': '#334155'
        }
        
    def create_header(self):
        """Создает заголовок с индикаторами."""
        header = tk.Frame(self.root, bg='#1a1f3a', height=80)
        header.pack(fill=tk.X, padx=15, pady=(10, 5))
        
        # Левая часть - логотип и название
        left_header = tk.Frame(header, bg='#1a1f3a')
        left_header.pack(side=tk.LEFT, fill=tk.Y, padx=20, pady=15)
        
        tk.Label(
            left_header,
            text="🛡️ NETWORK GUARDIAN",
            bg='#1a1f3a',
            fg='#3b82f6',
            font=('Arial', 24, 'bold')
        ).pack(anchor=tk.W)
        
        tk.Label(
            left_header,
            text="Advanced Network Security System",
            bg='#1a1f3a',
            fg='#94a3b8',
            font=('Arial', 10)
        ).pack(anchor=tk.W)
        
        # Правая часть - индикаторы статуса
        right_header = tk.Frame(header, bg='#1a1f3a')
        right_header.pack(side=tk.RIGHT, fill=tk.Y, padx=20, pady=15)
        
        self.status_indicator = tk.Label(
            right_header,
            text="● OFFLINE",
            bg='#1a1f3a',
            fg='#ef4444',
            font=('Arial', 14, 'bold')
        )
        self.status_indicator.pack(anchor=tk.E)
        
        self.time_label = tk.Label(
            right_header,
            text="",
            bg='#1a1f3a',
            fg='#94a3b8',
            font=('Arial', 10)
        )
        self.time_label.pack(anchor=tk.E)
        
    def create_control_cards(self, parent):
        """Создает карточки управления."""
        
        # Карточка управления
        control_card = self.create_card(parent, "⚙️ УПРАВЛЕНИЕ")
        
        # Кнопка запуска
        self.start_btn = tk.Button(
            control_card,
            text="▶ ЗАПУСТИТЬ ЗАЩИТУ",
            command=self.toggle_monitoring,
            bg='#10b981',
            fg='white',
            font=('Arial', 12, 'bold'),
            relief=tk.FLAT,
            bd=0,
            padx=20,
            pady=15,
            cursor="hand2",
            activebackground='#059669'
        )
        self.start_btn.pack(fill=tk.X, pady=(0, 15))
        
        # Поля настроек
        self.create_input_field(control_card, "Интерфейс:", "interface_var", "any")
        self.create_input_field(control_card, "BPF Фильтр:", "filter_var", "")
        
        # Правила обнаружения
        rules_label = tk.Label(
            control_card,
            text="ПРАВИЛА ОБНАРУЖЕНИЯ:",
            bg='#1a1f3a',
            fg='#94a3b8',
            font=('Arial', 9, 'bold')
        )
        rules_label.pack(anchor=tk.W, pady=(10, 5))
        
        self.detection_rules = {}
        rules = [
            ("port_scan", "🔍 Сканирование портов"),
            ("syn_flood", "⚡ SYN Flood атака"),
            ("icmp_flood", "📡 ICMP Flood атака"),
            ("udp_flood", "💥 UDP Flood атака"),
            ("large_packets", "📦 Большие пакеты"),
            ("connection_limit", "🔗 Превышение лимита соединений"),
            ("suspicious_ports", "🚪 Подозрительные порты")
        ]
        
        for key, label in rules:
            var = tk.BooleanVar(value=True)
            self.detection_rules[key] = var
            
            cb_frame = tk.Frame(control_card, bg='#1a1f3a')
            cb_frame.pack(fill=tk.X, pady=2)
            
            cb = tk.Checkbutton(
                cb_frame,
                text=label,
                variable=var,
                bg='#1a1f3a',
                fg='#e2e8f0',
                font=('Arial', 9),
                selectcolor='#0a0e27',
                activebackground='#1a1f3a',
                activeforeground='#3b82f6',
                cursor="hand2",
                command=lambda k=key: self.toggle_rule(k)
            )
            cb.pack(anchor=tk.W, padx=5)
        
        # Дополнительные кнопки
        btn_frame = tk.Frame(control_card, bg='#1a1f3a')
        btn_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.create_action_button(
            btn_frame,
            "🗑️ ОЧИСТИТЬ",
            self.clear_logs,
            '#6366f1'
        ).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 5))
        
        self.create_action_button(
            btn_frame,
            "🔓 РАЗБЛОК.",
            self.clear_all_blocks,
            '#ef4444'
        ).pack(side=tk.RIGHT, expand=True, fill=tk.X, padx=(5, 0))
        
        # Карточка статистики
        stats_card = self.create_card(parent, "📊 СТАТИСТИКА")
        
        self.stat_widgets = {}
        stats = [
            ("packets", "Всего пакетов", "0", "#3b82f6"),
            ("threats", "Угроз", "0", "#ef4444"),
            ("blocked", "Блокировок", "0", "#f59e0b"),
            ("rate", "Скорость", "0 пак/с", "#10b981")
        ]
        
        for key, label, value, color in stats:
            self.create_stat_item(stats_card, label, value, color, key)
        
        # Карточка заблокированных IP
        blocked_card = self.create_card(parent, "🚫 ЗАБЛОКИРОВАННЫЕ IP")
        
        # Список с прокруткой
        scroll_frame = tk.Frame(blocked_card, bg='#1a1f3a')
        scroll_frame.pack(fill=tk.BOTH, expand=True)
        
        scrollbar = tk.Scrollbar(scroll_frame, bg='#334155')
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.blocked_list = tk.Listbox(
            scroll_frame,
            bg='#0a0e27',
            fg='#e2e8f0',
            font=('Courier New', 9),
            selectbackground='#3b82f6',
            selectforeground='white',
            relief=tk.FLAT,
            bd=0,
            yscrollcommand=scrollbar.set,
            highlightthickness=0
        )
        self.blocked_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.blocked_list.yview)
        
        # Кнопка разблокировки
        self.create_action_button(
            blocked_card,
            "🔓 РАЗБЛОКИРОВАТЬ",
            self.unblock_selected,
            '#8b5cf6'
        ).pack(fill=tk.X, pady=(10, 0))
        
    def create_card(self, parent, title):
        """Создает карточку с заголовком."""
        card_frame = tk.Frame(parent, bg='#1a1f3a', relief=tk.FLAT, bd=0)
        card_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        
        # Заголовок
        header = tk.Frame(card_frame, bg='#242947', height=45)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        
        tk.Label(
            header,
            text=title,
            bg='#242947',
            fg='#e2e8f0',
            font=('Arial', 11, 'bold')
        ).pack(side=tk.LEFT, padx=15, pady=10)
        
        # Контент
        content = tk.Frame(card_frame, bg='#1a1f3a')
        content.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        return content
        
    def create_input_field(self, parent, label, var_name, default):
        """Создает поле ввода."""
        frame = tk.Frame(parent, bg='#1a1f3a')
        frame.pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(
            frame,
            text=label,
            bg='#1a1f3a',
            fg='#94a3b8',
            font=('Arial', 9)
        ).pack(anchor=tk.W, pady=(0, 5))
        
        var = tk.StringVar(value=default)
        setattr(self, var_name, var)
        
        entry = tk.Entry(
            frame,
            textvariable=var,
            bg='#0a0e27',
            fg='#e2e8f0',
            font=('Arial', 10),
            relief=tk.FLAT,
            bd=0,
            insertbackground='#3b82f6'
        )
        entry.pack(fill=tk.X, ipady=8, ipadx=10)
        
    def create_action_button(self, parent, text, command, color):
        """Создает кнопку действия."""
        return tk.Button(
            parent,
            text=text,
            command=command,
            bg=color,
            fg='white',
            font=('Arial', 9, 'bold'),
            relief=tk.FLAT,
            bd=0,
            padx=10,
            pady=8,
            cursor="hand2",
            activebackground=color
        )
        
    def create_stat_item(self, parent, label, value, color, key):
        """Создает элемент статистики."""
        frame = tk.Frame(parent, bg='#0a0e27', relief=tk.FLAT, bd=0)
        frame.pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(
            frame,
            text=label,
            bg='#0a0e27',
            fg='#94a3b8',
            font=('Arial', 9)
        ).pack(side=tk.LEFT, padx=10, pady=8)
        
        value_label = tk.Label(
            frame,
            text=value,
            bg='#0a0e27',
            fg=color,
            font=('Arial', 14, 'bold')
        )
        value_label.pack(side=tk.RIGHT, padx=10, pady=8)
        
        self.stat_widgets[key] = value_label
        
    def toggle_rule(self, rule_key):
        """Переключает правило обнаружения."""
        enabled = self.detection_rules[rule_key].get()
        status = "активировано" if enabled else "деактивировано"
        self.log_message(f"Правило '{rule_key}' {status}", "info")
        
        # Обновляем правила в анализаторе
        self.update_analyzer_rules()
    
    def update_analyzer_rules(self):
        """Обновляет активные правила в анализаторе."""
        active_rules = {
            key: var.get() 
            for key, var in self.detection_rules.items()
        }
        # Здесь можно передать правила в analyzer
        self.analyzer.active_rules = active_rules
        
    def create_events_panel(self, parent):
        """Создает панель событий."""
        
        # Критические события
        events_card = self.create_card(parent, "🔴 КРИТИЧЕСКИЕ СОБЫТИЯ")
        
        self.events_text = tk.Text(
            events_card,
            wrap=tk.WORD,
            bg='#0a0e27',
            fg='#fbbf24',
            font=('Courier New', 9),
            relief=tk.FLAT,
            bd=0,
            height=15,
            insertbackground='#fbbf24',
            selectbackground='#3b82f6'
        )
        self.events_text.pack(fill=tk.BOTH, expand=True)
        
        # Системные логи
        logs_card = self.create_card(parent, "📝 СИСТЕМНЫЕ ЛОГИ")
        
        self.logs_text = tk.Text(
            logs_card,
            wrap=tk.WORD,
            bg='#0a0e27',
            fg='#94a3b8',
            font=('Courier New', 8),
            relief=tk.FLAT,
            bd=0,
            height=12,
            insertbackground='#94a3b8',
            selectbackground='#3b82f6'
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
        
        try:
            self.monitor.start_monitoring(interface, filter_str)
            self.start_btn.configure(
                text="⏸ ОСТАНОВИТЬ ЗАЩИТУ",
                bg='#ef4444',
                activebackground='#dc2626'
            )
            self.status_indicator.configure(text="● ONLINE", fg='#10b981')
            self.log_message("🟢 Система защиты активирована", "success")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось запустить:\n{e}")
            self.log_message(f"🔴 Ошибка запуска: {e}", "error")
    
    def stop_monitoring(self):
        """Останавливает мониторинг."""
        self.monitor.stop_monitoring()
        self.start_btn.configure(
            text="▶ ЗАПУСТИТЬ ЗАЩИТУ",
            bg='#10b981',
            activebackground='#059669'
        )
        self.status_indicator.configure(text="● OFFLINE", fg='#ef4444')
        self.log_message("🔴 Система защиты деактивирована", "info")
    
    def on_packet_event(self, event_type, data):
        """Обработчик событий."""
        if event_type == "suspicious":
            self.log_threat(data)
        
        self.root.after(0, self.update_interface)
    
    def log_threat(self, data):
        """Логирует угрозу."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        reason = data.get("reason", "Unknown")
        details = data.get("details", {})
        src_ip = details.get("src_ip", "N/A")
        
        message = f"[{timestamp}] 🔴 {reason}\n"
        message += f"  └─ IP: {src_ip}\n\n"
        
        self.events_text.insert("1.0", message)
        
        # Ограничиваем размер
        lines = int(self.events_text.index('end-1c').split('.')[0])
        if lines > 200:
            self.events_text.delete("200.0", tk.END)
    
    def log_message(self, message, level="info"):
        """Логирует сообщение."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        icon = {"info": "ℹ️", "success": "✅", "error": "❌"}.get(level, "ℹ️")
        
        log_entry = f"[{timestamp}] {icon} {message}\n"
        self.logs_text.insert("1.0", log_entry)
        
        lines = int(self.logs_text.index('end-1c').split('.')[0])
        if lines > 150:
            self.logs_text.delete("150.0", tk.END)
    
    def update_interface(self):
        """Обновляет интерфейс."""
        # Время
        self.time_label.configure(text=datetime.now().strftime("%H:%M:%S"))
        
        # Статистика
        stats = self.monitor.get_statistics()
        self.stat_widgets["packets"].configure(text=str(stats["total_packets"]))
        self.stat_widgets["threats"].configure(text=str(stats["suspicious_packets"]))
        self.stat_widgets["blocked"].configure(text=str(stats["blocked_ips"]))
        
        self.update_blocked_list()
        
        # Повторяем обновление
        if self.monitor.is_running:
            self.root.after(1000, self.update_interface)
        else:
            self.root.after(2000, self.update_interface)
    
    def update_blocked_list(self):
        """Обновляет список блокировок."""
        self.blocked_list.delete(0, tk.END)
        blocked_ips = self.firewall.get_blocked_list()
        
        for ip, info in blocked_ips.items():
            reason = info.get("reason", "N/A")[:20]
            timestamp = info.get("timestamp", "N/A")[11:19]
            self.blocked_list.insert(tk.END, f"[{timestamp}] {ip} | {reason}")
    
    def unblock_selected(self):
        """Разблокирует выбранный IP."""
        selection = self.blocked_list.curselection()
        if not selection:
            messagebox.showwarning("Предупреждение", "Выберите IP")
            return
        
        item = self.blocked_list.get(selection[0])
        ip = item.split("] ")[1].split(" | ")[0]
        
        if messagebox.askyesno("Подтверждение", f"Разблокировать {ip}?"):
            self.firewall.unblock_ip(ip)
            self.analyzer.remove_from_blocklist(ip)
            self.log_message(f"Разблокирован IP: {ip}", "success")
    
    def clear_all_blocks(self):
        """Снимает все блокировки."""
        if messagebox.askyesno("Подтверждение", "Снять все блокировки?"):
            self.firewall.clear_all_blocks()
            self.analyzer.suspicious_ips.clear()
            self.log_message("Все блокировки сняты", "success")
    
    def clear_logs(self):
        """Очищает логи."""
        self.logs_text.delete(1.0, tk.END)
        self.events_text.delete(1.0, tk.END)
        self.log_message("Логи очищены", "info")


def main():
    """Главная функция."""
    root = tk.Tk()
    app = ModernTrafficMonitorGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
