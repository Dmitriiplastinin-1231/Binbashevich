import asyncio
import threading
import tkinter as tk
from tkinter.scrolledtext import ScrolledText
from tkinter import ttk, filedialog, simpledialog
import queue
import os
import sys

HOST = "127.0.0.1"
PORT = 8888

# ---------------- Асинхронная сетка (без изменений) ----------------

async def network_task(reader, writer, in_q, out_q):
    async def read_loop():
        try:
            while True:
                line = await reader.readline()
                if not line:
                    in_q.put("[Отключено от сервера]")
                    break
                line = line.decode().rstrip()
                in_q.put(line)
        except Exception as e:
            in_q.put(f"Ошибка чтения: {e}")

    async def write_loop():
        try:
            while True:
                msg = await asyncio.get_event_loop().run_in_executor(None, out_q.get)
                if msg == "/quit":
                    break
                if isinstance(msg, bytes):
                    writer.write(msg)
                else:
                    writer.write((msg + "\n").encode())
                await writer.drain()
        except Exception as e:
            in_q.put(f"Ошибка отправки: {e}")

    try:
        await asyncio.gather(read_loop(), write_loop())
    except Exception as e:
        in_q.put(f"Сетевая ошибка: {e}")
    finally:
        writer.close()
        await writer.wait_closed()

async def start_connection(host, port, in_q, out_q):
    try:
        reader, writer = await asyncio.open_connection(host, port)
        in_q.put("✓ Подключено к серверу")
        await network_task(reader, writer, in_q, out_q)
    except Exception as e:
        in_q.put(f"❌ Не удалось подключиться: {e}")

def run_async_thread(host, port, in_q, out_q):
    """Запуск асинхронного кода в отдельном потоке"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(start_connection(host, port, in_q, out_q))
    except Exception as e:
        in_q.put(f"Ошибка в потоке: {e}")
    finally:
        loop.close()

# ---------------- Новый современный GUI ----------------

class ModernChatGUI:
    def __init__(self, root):
        self.root = root
        root.title("NeoChat")
        root.configure(bg='#1a1a1a')
        root.geometry("900x700")
        
        # Центрируем окно
        root.update_idletasks()
        x = (root.winfo_screenwidth() - root.winfo_reqwidth()) // 2
        y = (root.winfo_screenheight() - root.winfo_reqheight()) // 2
        root.geometry(f"+{x}+{y}")
        
        # Современная цветовая схема
        self.colors = {
            'bg_primary': '#1a1a1a',
            'bg_secondary': '#2d2d2d',
            'bg_tertiary': '#3d3d3d',
            'accent_primary': '#5865f2',
            'accent_secondary': '#4752c4',
            'accent_success': '#57f287',
            'accent_danger': '#ed4245',
            'accent_warning': '#faa81a',
            'text_primary': '#ffffff',
            'text_secondary': '#b9bbbe',
            'text_muted': '#72767d'
        }

        # Настройка стилей
        self.setup_styles()
        
        # Создание основного layout
        self.create_main_layout()
        
        # Инициализация сетевых компонентов
        self.in_q = queue.Queue()
        self.out_q = queue.Queue()

        self.root.protocol("WM_DELETE_WINDOW", self.quit_app)
        
        # Настройка тегов для текста
        self.setup_text_tags()
        
        self.update_gui()
        self.start_network_thread()

    def setup_styles(self):
        """Настройка современных стилей"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Стиль для основных кнопок
        style.configure('Accent.TButton',
                       background=self.colors['accent_primary'],
                       foreground=self.colors['text_primary'],
                       borderwidth=0,
                       focuscolor='none',
                       padding=(20, 10),
                       font=('Segoe UI', 9, 'bold'))
        style.map('Accent.TButton',
                 background=[('active', self.colors['accent_secondary']),
                           ('pressed', self.colors['accent_secondary'])])
        
        # Стиль для второстепенных кнопок
        style.configure('Secondary.TButton',
                       background=self.colors['bg_tertiary'],
                       foreground=self.colors['text_primary'],
                       borderwidth=0,
                       focuscolor='none',
                       padding=(15, 8),
                       font=('Segoe UI', 9))
        style.map('Secondary.TButton',
                 background=[('active', '#4d4d4d'),
                           ('pressed', '#4d4d4d')])
        
        # Стиль для полей ввода
        style.configure('Modern.TEntry',
                       fieldbackground=self.colors['bg_tertiary'],
                       foreground=self.colors['text_primary'],
                       borderwidth=0,
                       insertcolor=self.colors['text_primary'],
                       padding=(10, 8))

    def create_main_layout(self):
        """Создание современного layout"""
        # Основной контейнер
        main_container = tk.Frame(self.root, bg=self.colors['bg_primary'])
        main_container.pack(fill='both', expand=True, padx=0, pady=0)
        
        # Боковая панель
        self.create_sidebar(main_container)
        
        # Разделитель
        separator = ttk.Separator(main_container, orient='vertical')
        separator.pack(side='left', fill='y', padx=0)
        
        # Основная область чата
        self.create_chat_area(main_container)

    def create_sidebar(self, parent):
        """Создание боковой панели"""
        sidebar = tk.Frame(parent, bg=self.colors['bg_secondary'], width=250)
        sidebar.pack(side='left', fill='y', padx=0, pady=0)
        sidebar.pack_propagate(False)
        
        # Заголовок
        title_frame = tk.Frame(sidebar, bg=self.colors['bg_secondary'], height=80)
        title_frame.pack(fill='x', pady=(0, 10))
        title_frame.pack_propagate(False)
        
        tk.Label(title_frame, text="NEOCHAT", 
                font=('Segoe UI', 16, 'bold'),
                fg=self.colors['accent_primary'],
                bg=self.colors['bg_secondary']).pack(expand=True)
        
        # Статус подключения
        self.status_indicator = tk.Frame(sidebar, bg=self.colors['accent_danger'], height=3)
        self.status_indicator.pack(fill='x', padx=20, pady=(0, 20))
        
        self.status_label = tk.Label(sidebar, 
                                   text="Не подключено", 
                                   font=('Segoe UI', 9),
                                   fg=self.colors['text_muted'],
                                   bg=self.colors['bg_secondary'])
        self.status_label.pack(pady=(0, 20))
        
        # Панель пользователя
        user_frame = tk.Frame(sidebar, bg=self.colors['bg_tertiary'], padx=15, pady=15)
        user_frame.pack(fill='x', padx=15, pady=(0, 15))
        
        tk.Label(user_frame, text="ПРОФИЛЬ", 
                font=('Segoe UI', 10, 'bold'),
                fg=self.colors['text_secondary'],
                bg=self.colors['bg_tertiary']).pack(anchor='w')
        
        # Ввод ника
        nick_frame = tk.Frame(user_frame, bg=self.colors['bg_tertiary'])
        nick_frame.pack(fill='x', pady=(10, 5))
        
        tk.Label(nick_frame, text="Ваше имя:", 
                font=('Segoe UI', 8),
                fg=self.colors['text_muted'],
                bg=self.colors['bg_tertiary']).pack(anchor='w')
        
        self.nick_entry = ttk.Entry(nick_frame, 
                                  style='Modern.TEntry',
                                  font=('Segoe UI', 10),
                                  width=20)
        self.nick_entry.pack(fill='x', pady=(5, 0))
        self.nick_entry.bind('<Return>', lambda e: self.set_nick())
        
        ttk.Button(nick_frame, 
                 text="Установить имя",
                 style='Secondary.TButton',
                 command=self.set_nick).pack(fill='x', pady=(8, 0))
        
        # Ввод комнаты
        room_frame = tk.Frame(user_frame, bg=self.colors['bg_tertiary'])
        room_frame.pack(fill='x', pady=(10, 0))
        
        tk.Label(room_frame, text="Комната:", 
                font=('Segoe UI', 8),
                fg=self.colors['text_muted'],
                bg=self.colors['bg_tertiary']).pack(anchor='w')
        
        self.room_entry = ttk.Entry(room_frame, 
                                  style='Modern.TEntry',
                                  font=('Segoe UI', 10),
                                  width=20)
        self.room_entry.pack(fill='x', pady=(5, 0))
        self.room_entry.bind('<Return>', lambda e: self.join_room())
        
        ttk.Button(room_frame, 
                 text="Войти в комнату",
                 style='Secondary.TButton',
                 command=self.join_room).pack(fill='x', pady=(8, 0))
        
        # Быстрые действия
        actions_frame = tk.Frame(sidebar, bg=self.colors['bg_secondary'])
        actions_frame.pack(fill='x', padx=15, pady=(0, 15))
        
        tk.Label(actions_frame, text="БЫСТРЫЕ ДЕЙСТВИЯ", 
                font=('Segoe UI', 10, 'bold'),
                fg=self.colors['text_secondary'],
                bg=self.colors['bg_secondary']).pack(anchor='w', pady=(0, 10))
        
        # Кнопки действий
        actions = [
            ("💬 Личное сообщение", self.send_private_message),
            ("📁 Отправить файл", self.send_file),
            ("👥 Список комнат", self.list_rooms),
            ("🔄 Сбросить настройки", self.reset_settings)
        ]
        
        for text, command in actions:
            btn = ttk.Button(actions_frame, 
                           text=text,
                           style='Secondary.TButton',
                           command=command)
            btn.pack(fill='x', pady=(0, 8))

    def create_chat_area(self, parent):
        """Создание области чата"""
        chat_container = tk.Frame(parent, bg=self.colors['bg_primary'])
        chat_container.pack(side='left', fill='both', expand=True, padx=0, pady=0)
        
        # Заголовок чата
        chat_header = tk.Frame(chat_container, bg=self.colors['bg_secondary'], height=60)
        chat_header.pack(fill='x', padx=0, pady=0)
        chat_header.pack_propagate(False)
        
        self.chat_title = tk.Label(chat_header, 
                                 text="ОБЩИЙ ЧАТ",
                                 font=('Segoe UI', 12, 'bold'),
                                 fg=self.colors['text_primary'],
                                 bg=self.colors['bg_secondary'])
        self.chat_title.pack(side='left', padx=20, pady=20)
        
        # Область сообщений
        messages_frame = tk.Frame(chat_container, bg=self.colors['bg_primary'])
        messages_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        self.output = ScrolledText(messages_frame, 
                                 state="disabled", 
                                 width=60, 
                                 height=20,
                                 font=('Segoe UI', 10),
                                 bg=self.colors['bg_secondary'],
                                 fg=self.colors['text_primary'],
                                 borderwidth=0,
                                 relief='flat',
                                 padx=15,
                                 pady=15,
                                 insertbackground=self.colors['text_primary'])
        self.output.pack(fill='both', expand=True)
        
        # Панель ввода
        input_frame = tk.Frame(chat_container, bg=self.colors['bg_primary'], padx=20, pady=20)
        input_frame.pack(fill='x', padx=0, pady=0)
        
        input_container = tk.Frame(input_frame, bg=self.colors['bg_tertiary'], relief='flat', bd=0)
        input_container.pack(fill='x', padx=0, pady=0)
        
        self.entry = ttk.Entry(input_container, 
                             style='Modern.TEntry',
                             font=('Segoe UI', 11))
        self.entry.pack(side='left', fill='x', expand=True, padx=15, pady=12)
        self.entry.bind('<Return>', lambda e: self.send_message())
        
        send_btn = ttk.Button(input_container, 
                            text="➤",
                            style='Accent.TButton',
                            command=self.send_message,
                            width=3)
        send_btn.pack(side='right', padx=10, pady=8)

    def setup_text_tags(self):
        """Настройка стилей текста"""
        tags_config = {
            "success": {"foreground": self.colors['accent_success'], "font": ('Segoe UI', 10, 'bold')},
            "error": {"foreground": self.colors['accent_danger'], "font": ('Segoe UI', 10)},
            "info": {"foreground": self.colors['accent_primary'], "font": ('Segoe UI', 10)},
            "warning": {"foreground": self.colors['accent_warning'], "font": ('Segoe UI', 10)},
            "private": {"foreground": '#bf7fff', "font": ('Segoe UI', 10, 'bold')},
            "system": {"foreground": self.colors['text_muted'], "font": ('Segoe UI', 9, 'italic')},
            "command": {"foreground": self.colors['text_muted'], "font": ('Segoe UI', 9)},
            "timestamp": {"foreground": self.colors['text_muted'], "font": ('Segoe UI', 8)},
            "username": {"foreground": '#faa81a', "font": ('Segoe UI', 10, 'bold')},
            "message": {"foreground": self.colors['text_primary'], "font": ('Segoe UI', 10)}
        }
        
        for tag_name, config in tags_config.items():
            self.output.tag_config(tag_name, **config)

    def set_nick(self):
        """Установка ника"""
        nick = self.nick_entry.get().strip()
        if nick:
            self.out_q.put(f"/nick {nick}")
            self.append_message(f"> Установка имени: {nick}", "command")

    def join_room(self):
        """Вход в комнату"""
        room = self.room_entry.get().strip()
        if room:
            self.out_q.put(f"/join {room}")
            self.append_message(f"> Вход в комнату: {room}", "command")

    def send_private_message(self):
        """Отправка личного сообщения"""
        target = simpledialog.askstring("Личное сообщение", "Получатель:", initialvalue="")
        if target:
            message = simpledialog.askstring("Личное сообщение", "Сообщение:", initialvalue="")
            if message:
                self.out_q.put(f"/pm {target} {message}")
                self.append_message(f"> Личное сообщение для {target}", "command")

    def send_file(self):
        """Отправка файла"""
        file_path = filedialog.askopenfilename(
            title="Выберите файл для отправки",
            filetypes=[("Все файлы", "*.*")]
        )
        if file_path:
            self.out_q.put(f"/sendfile {os.path.basename(file_path)}")
            try:
                with open(file_path, "rb") as f:
                    file_data = f.read()
                self.out_q.put(file_data)
                self.append_message(f"> Отправка файла: {os.path.basename(file_path)}", "command")
            except Exception as e:
                self.append_message(f"❌ Ошибка отправки файла: {e}", "error")

    def list_rooms(self):
        """Запрос списка комнат"""
        self.out_q.put("/rooms")
        self.append_message("> Запрос списка комнат", "command")

    def reset_settings(self):
        """Сброс настроек"""
        self.nick_entry.delete(0, tk.END)
        self.room_entry.delete(0, tk.END)
        self.append_message("> Настройки сброшены", "system")

    def append_message(self, text, tag="message"):
        """Добавление сообщения в чат"""
        self.output.config(state="normal")
        
        # Добавляем timestamp
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M")
        self.output.insert("end", f"[{timestamp}] ", "timestamp")
        
        self.output.insert("end", text + "\n", tag)
        self.output.see("end")
        self.output.config(state="disabled")

    def update_gui(self):
        """Обновление интерфейса"""
        try:
            while True:
                msg = self.in_q.get_nowait()
                
                # Автоматическое определение типа сообщения для стилизации
                if msg.startswith("✓"):
                    tag = "success"
                    self.status_indicator.config(bg=self.colors['accent_success'])
                    self.status_label.config(text="Подключено", fg=self.colors['accent_success'])
                elif msg.startswith("❌") or "Ошибка" in msg or "Не удалось" in msg:
                    tag = "error"
                    self.status_indicator.config(bg=self.colors['accent_danger'])
                    self.status_label.config(text="Ошибка", fg=self.colors['accent_danger'])
                elif msg.startswith("[PM") or "личное" in msg.lower():
                    tag = "private"
                elif msg.startswith("Вы вошли") or "комната" in msg.lower():
                    tag = "info"
                    if "Вы вошли в комнату" in msg:
                        room = msg.split(" ")[-1]
                        self.chat_title.config(text=f"КОМНАТА: {room.upper()}")
                elif "файл" in msg.lower():
                    tag = "warning"
                elif msg.startswith("Комнаты:") or msg.startswith("Список комнат"):
                    tag = "system"
                elif msg.startswith("> /"):
                    tag = "command"
                elif "установлен" in msg.lower():
                    tag = "success"
                else:
                    tag = "message"
                
                self.append_message(msg, tag)
                    
        except queue.Empty:
            pass
        self.root.after(100, self.update_gui)

    def send_message(self):
        """Отправка сообщения"""
        msg = self.entry.get().strip()
        if not msg:
            return

        self.out_q.put(msg)
        self.entry.delete(0, "end")

    def start_network_thread(self):
        """Запуск сетевого потока"""
        thread = threading.Thread(
            target=run_async_thread,
            args=(HOST, PORT, self.in_q, self.out_q),
            daemon=True
        )
        thread.start()

    def quit_app(self):
        """Выход из приложения"""
        self.append_message("🔌 Отключение от сервера...", "system")
        self.out_q.put("/quit")
        self.root.after(300, self.root.destroy)

def start_gui():
    """Запуск GUI"""
    print("=" * 50)
    print("NeoChat - Современный клиент чата")
    print("=" * 50)
    print("Перед запуском убедитесь, что сервер запущен:")
    print(f"  python server.py")
    print("=" * 50)
    
    root = tk.Tk()
    app = ModernChatGUI(root)
    root.mainloop()

# ---------------- Запуск ----------------

if __name__ == "__main__":
    start_gui()