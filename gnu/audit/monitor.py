import time
import threading
import os
import psutil
import pwd
import grp

# Безопасный импорт datetime
try:
    from datetime import datetime
    DATETIME_AVAILABLE = True
except ImportError:
    DATETIME_AVAILABLE = False
    print("⚠️ datetime не доступен, будут использоваться временные метки без точного времени")

# Безопасные импорты дополнительных модулей
try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
    WATCHDOG_AVAILABLE = True
except ImportError:
    WATCHDOG_AVAILABLE = False
    print("⚠️ watchdog не установлен, файловый мониторинг будет в демо-режиме")

try:
    from config import EXCLUDED_PATTERNS, EXCLUDED_PROCESSES
except ImportError:
    EXCLUDED_PATTERNS = []
    EXCLUDED_PROCESSES = []
    print("⚠️ config не найден, используются пустые списки исключений")

def get_timestamp():
    """Безопасное получение временной метки"""
    if DATETIME_AVAILABLE:
        return datetime.now().isoformat()
    else:
        return str(time.time())

class SecurityManager:
    """Менеджер безопасности для ограничения привилегий."""
    
    @staticmethod
    def drop_privileges(username='nobody'):
        """Понижает привилегии до указанного пользователя."""
        try:
            # Получаем UID и GID целевого пользователя
            user_info = pwd.getpwnam(username)
            uid = user_info.pw_uid
            gid = user_info.pw_gid
            
            # Устанавливаем дополнительные группы
            os.setgroups([])
            
            # Сначала устанавливаем GID, затем UID
            os.setgid(gid)
            os.setuid(uid)
            
            # Устанавливаем безопасную маску создания файлов
            os.umask(0o077)
            
            print(f"🔒 Привилегии понижены до пользователя: {username}")
            
        except Exception as e:
            print(f"❌ Ошибка понижения привилегий: {e}")
            raise

class ProcessMonitor:
    """Реальный мониторинг процессов."""
    
    stop_flag = False

    @classmethod
    def monitor_processes(cls, callback):
        """Реальный мониторинг запуска и завершения процессов."""
        print("🔍 Запуск мониторинга процессов...")
        
        try:
            current_processes = set(p.pid for p in psutil.process_iter())
        except Exception as e:
            print(f"❌ Ошибка инициализации мониторинга процессов: {e}")
            return
        
        while not cls.stop_flag:
            time.sleep(2)
            
            try:
                updated_processes = set(p.pid for p in psutil.process_iter())
                
                # Новые процессы
                new_processes = updated_processes - current_processes
                for pid in new_processes:
                    try:
                        proc = psutil.Process(pid)
                        process_name = proc.name()
                        
                        if not cls._is_excluded_process(process_name):
                            callback("process_start", {
                                "pid": pid, 
                                "name": process_name, 
                                "user": proc.username(),
                                "timestamp": get_timestamp()
                            })
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass
                    except Exception as e:
                        print(f"⚠️ Ошибка обработки нового процесса {pid}: {e}")
                
                # Завершенные процессы
                terminated_processes = current_processes - updated_processes
                for pid in terminated_processes:
                    callback("process_end", {
                        "pid": pid,
                        "timestamp": get_timestamp()
                    })
                
                current_processes = updated_processes
                
            except Exception as e:
                print(f"❌ Ошибка мониторинга процессов: {e}")
                time.sleep(5)

    @staticmethod
    def _is_excluded_process(process_name):
        """Проверяет, является ли процесс исключенным."""
        try:
            return any(excluded in process_name.lower() for excluded in EXCLUDED_PROCESSES)
        except:
            return False

    @classmethod
    def stop_monitoring(cls):
        cls.stop_flag = True
        print("⏹️ Мониторинг процессов остановлен")

class NetworkMonitor:
    """Реальный мониторинг сети."""
    
    stop_flag = False

    @classmethod
    def monitor_network(cls, callback):
        """Реальный мониторинг сетевых подключений."""
        print("🌐 Запуск мониторинга сети...")
        previous_connections = set()
        
        while not cls.stop_flag:
            time.sleep(3)
            
            try:
                current_connections = set()
                for conn in psutil.net_connections(kind='inet'):
                    if conn.status == 'ESTABLISHED' and conn.raddr:
                        conn_key = (
                            conn.laddr.ip, conn.laddr.port,
                            conn.raddr.ip, conn.raddr.port,
                            conn.pid or 0
                        )
                        current_connections.add(conn_key)

                # Новые подключения
                new_connections = current_connections - previous_connections
                for conn in new_connections:
                    try:
                        proc_name = "Unknown"
                        if conn[4] > 0:
                            proc = psutil.Process(conn[4])
                            proc_name = proc.name()
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass
                    
                    callback("network_connection", {
                        "type": "established",
                        "local_address": f"{conn[0]}:{conn[1]}",
                        "remote_address": f"{conn[2]}:{conn[3]}",
                        "pid": conn[4],
                        "name": proc_name,
                        "timestamp": get_timestamp()
                    })

                # Закрытые подключения
                closed_connections = previous_connections - current_connections
                for conn in closed_connections:
                    callback("network_connection", {
                        "type": "closed", 
                        "local_address": f"{conn[0]}:{conn[1]}",
                        "remote_address": f"{conn[2]}:{conn[3]}",
                        "pid": conn[4],
                        "timestamp": get_timestamp()
                    })

                previous_connections = current_connections
                
            except Exception as e:
                print(f"❌ Ошибка мониторинга сети: {e}")
                time.sleep(5)

    @classmethod
    def stop_monitoring(cls):
        cls.stop_flag = True
        print("⏹️ Мониторинг сети остановлен")

# Файловый мониторинг
if WATCHDOG_AVAILABLE:
    class RealFileMonitor(FileSystemEventHandler):
        """Реальный мониторинг файловой системы с фильтрацией."""
        
        def __init__(self, callback):
            self.callback = callback

        def _is_excluded_file(self, file_path):
            """Проверяет, является ли файл исключенным."""
            try:
                abs_path = os.path.abspath(file_path)
                
                for pattern in EXCLUDED_PATTERNS:
                    if pattern in abs_path:
                        return True
                
                if os.path.basename(abs_path).startswith('.'):
                    return True
                    
                return False
            except:
                return False

        def on_created(self, event):
            if not event.is_directory and not self._is_excluded_file(event.src_path):
                self.callback("file_created", {
                    "path": os.path.abspath(event.src_path),
                    "timestamp": get_timestamp()
                })

        def on_modified(self, event):
            if not event.is_directory and not self._is_excluded_file(event.src_path):
                self.callback("file_modified", {
                    "path": os.path.abspath(event.src_path),
                    "timestamp": get_timestamp()
                })

        def on_deleted(self, event):
            if not event.is_directory and not self._is_excluded_file(event.src_path):
                self.callback("file_deleted", {
                    "path": os.path.abspath(event.src_path),
                    "timestamp": get_timestamp()
                })

    class FileMonitor:
        """Класс для управления реальным мониторингом файлов."""
        
        def __init__(self, callback):
            self.callback = callback
            self.observer = None
            self.monitoring = False

        def start_monitoring(self, path="."):
            """Запуск реального мониторинга файлов с фильтрацией."""
            try:
                self.observer = Observer()
                event_handler = RealFileMonitor(self.callback)
                
                home_dir = os.path.expanduser("~")
                current_dir = os.path.abspath(path)
                
                paths_to_watch = [home_dir, current_dir]
                
                for watch_path in paths_to_watch:
                    if os.path.exists(watch_path):
                        self.observer.schedule(event_handler, watch_path, recursive=True)
                        print(f"👁️  Мониторинг файлов в: {watch_path}")
                
                self.observer.start()
                self.monitoring = True
                self.callback("system", {"message": "Мониторинг файлов запущен"})
                
                while self.monitoring:
                    time.sleep(1)
                    
            except Exception as e:
                print(f"❌ Ошибка запуска мониторинга файлов: {e}")
                self.callback("system", {"message": f"Ошибка мониторинга файлов: {e}"})

        def stop_monitoring(self):
            """Остановка мониторинга файлов."""
            self.monitoring = False
            if self.observer:
                self.observer.stop()
                self.observer.join()
                self.callback("system", {"message": "Мониторинг файлов остановлен"})

else:
    # Демо-режим если watchdog не установлен
    class FileMonitor:
        def __init__(self, callback):
            self.callback = callback
            self.monitoring = False

        def start_monitoring(self, path="."):
            """Демо-режим мониторинга файлов."""
            self.monitoring = True
            self.callback("system", {"message": "Демо-мониторинг файлов запущен"})
            
            import random
            demo_files = [
                "/tmp/test_file.txt",
                os.path.join(os.path.expanduser("~"), "document.pdf"),
                "/var/log/system.log"
            ]
            
            while self.monitoring:
                time.sleep(10)
                if not self.monitoring:
                    break
                    
                event_type = random.choice(["file_created", "file_modified", "file_deleted"])
                self.callback(event_type, {
                    "path": random.choice(demo_files),
                    "timestamp": get_timestamp()
                })

        def stop_monitoring(self):
            self.monitoring = False
            self.callback("system", {"message": "Мониторинг файлов остановлен"})

def start_file_monitoring(callback, path="."):
    """Запуск мониторинга файлов."""
    monitor = FileMonitor(callback)
    thread = threading.Thread(target=monitor.start_monitoring, args=(path,), daemon=True)
    thread.start()
    return monitor