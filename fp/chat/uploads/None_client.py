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

# ---------------- Асинхронная сетка ----------------

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

# ---------------- GUI ----------------

class ChatGUI:
    def __init__(self, root):
        self.root = root
        root.title("Чат")
        root.configure(bg='#f0f0f0')
        root.geometry("700x600")
        
        # Центрируем окно
        root.update_idletasks()
        x = (root.winfo_screenwidth() - root.winfo_reqwidth()) // 2
        y = (root.winfo_screenheight() - root.winfo_reqheight()) // 2
        root.geometry(f"+{x}+{y}")
        
        self.colors = {
            'primary': '#4CAF50',
            'primary_dark': '#388E3C',
            'secondary': '#2196F3',
            'accent': '#FF9800',
            'background': '#f5f5f5',
            'surface': '#ffffff',
            'text_primary': '#212121',
            'text_secondary': '#757575'
        }

        # Создаем стиль для ttk виджетов
        style = ttk.Style()
        style.configure('Primary.TButton', 
                       background=self.colors['primary'],
                       foreground='white',
                       padding=(15, 8),
                       font=('Arial', 9, 'bold'))
        style.map('Primary.TButton',
                 background=[('active', self.colors['primary_dark']),
                           ('pressed', self.colors['primary_dark'])])
        
        style.configure('Secondary.TButton',
                       background=self.colors['secondary'],
                       foreground='white',
                       padding=(10, 6),
                       font=('Arial', 9))
        
        style.configure('Accent.TButton',
                       background=self.colors['accent'],
                       foreground='white',
                       padding=(10, 6),
                       font=('Arial', 9))

        # Основные фреймы
        main_frame = tk.Frame(root, bg=self.colors['background'], padx=10, pady=10)
        main_frame.pack(fill='both', expand=True)

        # Панель управления пользователем
        control_frame = tk.Frame(main_frame, bg=self.colors['surface'], relief='groove', bd=1)
        control_frame.pack(fill='x', pady=(0, 10))

        # Ввод ника
        nick_frame = tk.Frame(control_frame, bg=self.colors['surface'])
        nick_frame.pack(fill='x', padx=10, pady=5)
        
        tk.Label(nick_frame, text="Имя:", 
                font=('Arial', 9),
                fg=self.colors['text_primary'],
                bg=self.colors['surface']).pack(side='left')
        
        self.nick_entry = tk.Entry(nick_frame, 
                                 font=('Arial', 10),
                                 width=15,
                                 relief='solid',
                                 bd=1)
        self.nick_entry.pack(side='left', padx=(5, 5))
        self.nick_entry.bind('<Return>', lambda e: self.set_nick())
        
        self.nick_btn = ttk.Button(nick_frame, 
                                 text="Установить",
                                 style='Primary.TButton',
                                 command=self.set_nick)
        self.nick_btn.pack(side='left', padx=5)

        # Ввод комнаты
        room_frame = tk.Frame(control_frame, bg=self.colors['surface'])
        room_frame.pack(fill='x', padx=10, pady=5)
        
        tk.Label(room_frame, text="Комната:", 
                font=('Arial', 9),
                fg=self.colors['text_primary'],
                bg=self.colors['surface']).pack(side='left')
        
        self.room_entry = tk.Entry(room_frame, 
                                 font=('Arial', 10),
                                 width=15,
                                 relief='solid',
                                 bd=1)
        self.room_entry.pack(side='left', padx=(5, 5))
        self.room_entry.bind('<Return>', lambda e: self.join_room())
        
        self.room_btn = ttk.Button(room_frame, 
                                 text="Войти",
                                 style='Primary.TButton',
                                 command=self.join_room)
        self.room_btn.pack(side='left', padx=5)

        # Информационная панель
        info_frame = tk.Frame(control_frame, bg=self.colors['surface'])
        info_frame.pack(fill='x', padx=10, pady=5)
        
        self.status_label = tk.Label(info_frame, 
                                   text="🔴 Не подключено", 
                                   font=('Arial', 9),
                                   fg=self.colors['text_secondary'],
                                   bg=self.colors['surface'])
        self.status_label.pack(side='left')
        
        self.user_info_label = tk.Label(info_frame, 
                                      text="Имя: Гость | Комната: Не выбрана",
                                      font=('Arial', 9),
                                      fg=self.colors['text_secondary'],
                                      bg=self.colors['surface'])
        self.user_info_label.pack(side='right')

        # Область чата
        chat_container = tk.Frame(main_frame, bg=self.colors['surface'], relief='sunken', bd=1)
        chat_container.pack(fill='both', expand=True, pady=(0, 10))

        self.output = ScrolledText(chat_container, 
                                 state="disabled", 
                                 width=80, 
                                 height=20,
                                 font=('Arial', 10),
                                 bg='white',
                                 fg='black',
                                 relief='flat',
                                 padx=10,
                                 pady=10)
        self.output.pack(fill='both', expand=True, padx=1, pady=1)

        # Панель ввода сообщения
        input_frame = tk.Frame(main_frame, bg=self.colors['background'])
        input_frame.pack(fill='x', pady=(0, 10))

        # Поле ввода сообщения
        self.entry = tk.Entry(input_frame, 
                            font=('Arial', 11),
                            bg='white',
                            relief='solid',
                            bd=1)
        self.entry.pack(side='left', fill='x', expand=True, padx=(0, 10))
        self.entry.bind('<Return>', lambda e: self.send_message())

        # Кнопка отправки
        self.send_btn = ttk.Button(input_frame, 
                                 text="Отправить",
                                 style='Primary.TButton',
                                 command=self.send_message)
        self.send_btn.pack(side='left')

        # Панель функций
        functions_frame = tk.Frame(main_frame, bg=self.colors['background'])
        functions_frame.pack(fill='x')

        # Первый ряд кнопок
        row1_frame = tk.Frame(functions_frame, bg=self.colors['background'])
        row1_frame.pack(fill='x', pady=2)
        
        ttk.Button(row1_frame, 
                 text="Личное сообщение",
                 style='Secondary.TButton',
                 command=self.send_private_message).pack(side='left', padx=(0, 5))
        
        ttk.Button(row1_frame, 
                 text="Отправить файл",
                 style='Secondary.TButton',
                 command=self.send_file).pack(side='left', padx=(0, 5))
        
        ttk.Button(row1_frame, 
                 text="Список комнат",
                 style='Secondary.TButton',
                 command=self.list_rooms).pack(side='left', padx=(0, 5))

        # Второй ряд кнопок
        row2_frame = tk.Frame(functions_frame, bg=self.colors['background'])
        row2_frame.pack(fill='x', pady=2)
        
        ttk.Button(row2_frame, 
                 text="Сменить имя",
                 style='Secondary.TButton',
                 command=self.focus_nick).pack(side='left', padx=(0, 5))
        
        ttk.Button(row2_frame, 
                 text="Сменить комнату",
                 style='Secondary.TButton',
                 command=self.focus_room).pack(side='left', padx=(0, 5))
        
        ttk.Button(row2_frame, 
                 text="Выйти",
                 style='Accent.TButton',
                 command=self.quit_app).pack(side='right')

        self.in_q = queue.Queue()
        self.out_q = queue.Queue()

        self.root.protocol("WM_DELETE_WINDOW", self.quit_app)
        
        # Настройка стилей тегов для текста
        style_tags = [
            ("success", {'foreground': 'green', 'font': ('Arial', 10, 'bold')}),
            ("info", {'foreground': 'blue'}),
            ("private", {'foreground': 'purple', 'font': ('Arial', 10, 'bold')}),
            ("file", {'foreground': 'orange'}),
            ("command", {'foreground': 'gray', 'font': ('Arial', 9, 'italic')}),
            ("error", {'foreground': 'red'}),
            ("message", {'foreground': 'black'}),
            ("system", {'foreground': 'darkblue', 'font': ('Arial', 9)})
        ]
        
        for tag_name, tag_config in style_tags:
            self.output.tag_config(tag_name, **tag_config)

        self.update_gui()
        self.start_network_thread()

        # Фокус на поле ввода ника
        self.nick_entry.focus_set()

    def set_nick(self):
        """Установка ника"""
        nick = self.nick_entry.get().strip()
        if nick:
            self.out_q.put(f"/nick {nick}")
            self.user_info_label.config(text=f"Имя: {nick} | Комната: Не выбрана")
            self.append(f"> /nick {nick}", "command")

    def join_room(self):
        """Вход в комнату"""
        room = self.room_entry.get().strip()
        if room:
            self.out_q.put(f"/join {room}")
            self.append(f"> /join {room}", "command")

    def focus_nick(self):
        """Фокус на поле ввода ника"""
        self.nick_entry.focus_set()
        self.nick_entry.select_range(0, tk.END)

    def focus_room(self):
        """Фокус на поле ввода комнаты"""
        self.room_entry.focus_set()
        self.room_entry.select_range(0, tk.END)

    def send_private_message(self):
        """Отправка личного сообщения"""
        target = simpledialog.askstring("Личное сообщение", "Введите имя пользователя:")
        if target:
            message = simpledialog.askstring("Личное сообщение", "Введите сообщение:")
            if message:
                self.out_q.put(f"/pm {target} {message}")
                self.append(f"> /pm {target} {message}", "command")

    def send_file(self):
        """Отправка файла"""
        file_path = filedialog.askopenfilename(title="Выберите файл для отправки")
        if file_path:
            self.out_q.put(f"/sendfile {os.path.basename(file_path)}")
            try:
                with open(file_path, "rb") as f:
                    file_data = f.read()
                self.out_q.put(file_data)
                self.append(f"> /sendfile {os.path.basename(file_path)}", "command")
            except Exception as e:
                self.append(f"❌ Ошибка отправки файла: {e}", "error")

    def list_rooms(self):
        """Запрос списка комнат"""
        self.out_q.put("/rooms")
        self.append("> /rooms", "command")

    def append(self, text, tag="message"):
        """Добавляет текст в область чата с форматированием"""
        self.output.config(state="normal")
        
        # Автоматическое определение типа сообщения
        if tag == "message":
            if text.startswith("✓") or "установлен" in text:
                tag = "success"
            elif text.startswith("❌") or "Ошибка" in text or "Не удалось" in text:
                tag = "error"
            elif text.startswith("Вы вошли") or "Подключено" in text:
                tag = "info"
            elif text.startswith("[PM") or "Личное" in text:
                tag = "private"
            elif "Файл" in text:
                tag = "file"
            elif text.startswith("Комнаты:") or text.startswith("Список комнат"):
                tag = "system"
            elif text.startswith("> /"):
                tag = "command"
        
        self.output.insert("end", text + "\n", tag)
        self.output.see("end")
        self.output.config(state="disabled")

    def update_gui(self):
        """Обновление GUI из очереди"""
        try:
            while True:
                msg = self.in_q.get_nowait()
                self.append(msg)
                
                # Обновляем статус подключения
                if msg.startswith("✓ Подключено"):
                    self.status_label.config(text="🟢 Подключено", fg='green')
                elif msg.startswith("❌"):
                    self.status_label.config(text="🔴 Ошибка подключения", fg='red')
                
                # Обновляем информацию о пользователе
                if msg.startswith("Псевдоним установлен:"):
                    nick = msg.split(": ")[1]
                    current_text = self.user_info_label.cget("text")
                    if "Комната:" in current_text:
                        room = current_text.split("Комната: ")[1]
                        self.user_info_label.config(text=f"Имя: {nick} | Комната: {room}")
                    else:
                        self.user_info_label.config(text=f"Имя: {nick} | Комната: Не выбрана")
                
                # Обновляем информацию о комнате
                elif msg.startswith("Вы вошли в комнату"):
                    room = msg.split(" ")[-1]
                    current_text = self.user_info_label.cget("text")
                    if "Имя:" in current_text:
                        nick = current_text.split("Имя: ")[1].split(" |")[0]
                        self.user_info_label.config(text=f"Имя: {nick} | Комната: {room}")
                    else:
                        self.user_info_label.config(text=f"Имя: Гость | Комната: {room}")
                    
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
        self.append("🔌 Отключение от сервера...", "system")
        self.out_q.put("/quit")
        self.root.after(300, self.root.destroy)

def start_gui():
    """Запуск GUI"""
    print("=" * 50)
    print("Чат - Клиент")
    print("=" * 50)
    print("Перед запуском убедитесь, что сервер запущен:")
    print(f"  python server.py")
    print("=" * 50)
    
    root = tk.Tk()
    app = ChatGUI(root)
    root.mainloop()

# ---------------- Запуск ----------------

if __name__ == "__main__":
    start_gui()