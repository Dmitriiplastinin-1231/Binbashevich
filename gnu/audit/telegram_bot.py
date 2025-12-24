import asyncio
import logging
from pathlib import Path
from telegram import Bot
from telegram.error import TelegramError


class TelegramReporter:
    def __init__(self, token: str, chat_id: str):
        """
        Инициализация Telegram-бота
        
        Args:
            token: Токен бота от @BotFather
            chat_id: ID чата/пользователя для отправки сообщений
        """
        self.token = token
        self.chat_id = chat_id
        self.bot = None
        self.is_connected = False
        
    async def connect(self):
        """Подключение к боту"""
        try:
            self.bot = Bot(token=self.token)
            await self.bot.get_me()
            self.is_connected = True
            print("✅ Telegram бот подключен")
            return True
        except TelegramError as e:
            print(f"❌ Ошибка подключения Telegram бота: {e}")
            return False
    
    async def send_file(self, file_path: str, caption: str = ""):
        """
        Отправка файла в Telegram
        
        Args:
            file_path: Путь к файлу
            caption: Подпись к файлу
        """
        if not self.is_connected or not self.bot:
            if not await self.connect():
                return False
        
        try:
            file_path = Path(file_path)
            if not file_path.exists():
                print(f"❌ Файл не найден: {file_path}")
                return False
            
            with open(file_path, 'rb') as file:
                await self.bot.send_document(
                    chat_id=self.chat_id,
                    document=file,
                    caption=caption,
                    filename=file_path.name
                )
            print(f"✅ Файл отправлен в Telegram: {file_path.name}")
            return True
            
        except TelegramError as e:
            print(f"❌ Ошибка отправки файла: {e}")
            return False
        except Exception as e:
            print(f"❌ Неожиданная ошибка: {e}")
            return False
    
    async def send_message(self, text: str):
        """Отправка текстового сообщения"""
        if not self.is_connected or not self.bot:
            if not await self.connect():
                return False
        
        try:
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=text
            )
            return True
        except TelegramError as e:
            print(f"❌ Ошибка отправки сообщения: {e}")
            return False

# Синхронные обертки для использования в tkinter
class TelegramReporterSync:
    def __init__(self, token: str, chat_id: str):
        self.reporter = TelegramReporter(token, chat_id)
        self.loop = asyncio.new_event_loop()
        
    def connect(self):
        """Синхронное подключение"""
        return self.loop.run_until_complete(self.reporter.connect())
    
    def send_file(self, file_path: str, caption: str = ""):
        """Синхронная отправка файла"""
        return self.loop.run_until_complete(self.reporter.send_file(file_path, caption))
    
    def send_message(self, text: str):
        """Синхронная отправка сообщения"""
        return self.loop.run_until_complete(self.reporter.send_message(text))

# Утилита для работы с конфигурацией
import json
import os

class TelegramConfig:
    @staticmethod
    def load_config(config_file="telegram_config.json"):
        """Загрузка конфигурации из файла"""
        if not os.path.exists(config_file):
            return None
        
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            return config
        except Exception as e:
            print(f"❌ Ошибка загрузки конфигурации: {e}")
            return None
    
    @staticmethod
    def save_config(token: str, chat_id: str, config_file="telegram_config.json"):
        """Сохранение конфигурации в файл"""
        config = {
            "token": token,
            "chat_id": chat_id
        }
        
        try:
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"❌ Ошибка сохранения конфигурации: {e}")
            return False
    
    @staticmethod
    def create_config_dialog():
        """Диалог создания конфигурации"""
        import tkinter as tk
        from tkinter import ttk, messagebox
        
        def save_configuration():
            token = token_entry.get().strip()
            chat_id = chat_id_entry.get().strip()
            
            if not token or not chat_id:
                messagebox.showerror("Ошибка", "Заполните все поля!")
                return
            
            if TelegramConfig.save_config(token, chat_id):
                messagebox.showinfo("Успех", "Конфигурация сохранена!\n"
                                        "Файл: telegram_config.json")
                dialog.destroy()
            else:
                messagebox.showerror("Ошибка", "Не удалось сохранить конфигурацию")
        
        dialog = tk.Toplevel()
        dialog.title("Настройка Telegram бота")
        dialog.geometry("400x250")
        dialog.configure(bg='#1e1e1e')
        dialog.resizable(False, False)
        
        # Стили
        style = ttk.Style()
        style.configure('TLabel', background='#1e1e1e', foreground='#ffffff')
        style.configure('TEntry', fieldbackground='#252526', foreground='#ffffff')
        
        frame = ttk.Frame(dialog, padding=20)
        frame.pack(fill=tk.BOTH, expand=True)
        
        # Заголовок
        ttk.Label(frame, text="⚙️ Настройка Telegram бота", 
                 font=('Segoe UI', 14, 'bold')).pack(pady=(0, 20))
        
        # Поле для токена
        ttk.Label(frame, text="Токен бота (от @BotFather):").pack(anchor='w')
        token_entry = ttk.Entry(frame, width=40, style='TEntry')
        token_entry.pack(pady=(5, 15), fill=tk.X)
        
        # Поле для chat_id
        ttk.Label(frame, text="Chat ID (можно получить у @userinfobot):").pack(anchor='w')
        chat_id_entry = ttk.Entry(frame, width=40, style='TEntry')
        chat_id_entry.pack(pady=(5, 15), fill=tk.X)
        
        # Инструкция
        info_text = """Инструкция:
1. Создайте бота через @BotFather
2. Получите токен
3. Узнайте ваш Chat ID через @userinfobot"""
        
        ttk.Label(frame, text=info_text, foreground='#cccccc',
                 font=('Segoe UI', 9)).pack(pady=(0, 20))
        
        # Кнопки
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill=tk.X)
        
        ttk.Button(btn_frame, text="Сохранить", 
                  command=save_configuration).pack(side=tk.RIGHT, padx=(10, 0))
        ttk.Button(btn_frame, text="Отмена", 
                  command=dialog.destroy).pack(side=tk.RIGHT)