# loggerr.py
import json
import os
import gzip
from datetime import datetime  # ДОБАВЛЕНО: импорт datetime

try:
    from messenger import global_messenger
    from config import EXCLUDED_PATTERNS, EXCLUDED_PROCESSES
except ImportError:
    # Резервные значения если модули не найдены
    class MockMessenger:
        def send_message(self, *args, **kwargs):
            pass
    global_messenger = MockMessenger()
    EXCLUDED_PATTERNS = []
    EXCLUDED_PROCESSES = []

class EventLogger:
    """Класс для регистрации и управления системными событиями."""

    def __init__(self, log_file="audit_log.json", max_size_mb=10, archive_limit=5):
        self.log_file = log_file
        self.max_size_bytes = max_size_mb * 1024 * 1024
        self.archive_limit = archive_limit
        self.events = []
        self._load_events()
        print("✅ EventLogger инициализирован")

    def _load_events(self):
        """Загрузка существующих событий из файла."""
        try:
            if os.path.exists(self.log_file):
                with open(self.log_file, "r", encoding='utf-8') as f:
                    lines = f.readlines()
                    for line in lines:
                        if line.strip():
                            self.events.append(json.loads(line))
        except Exception as e:
            print(f"⚠️ Ошибка загрузки событий: {e}")
            self.events = []

    def _check_size_and_rotate(self):
        """Проверяет размер файла и выполняет архивацию при необходимости."""
        try:
            if (os.path.exists(self.log_file) and 
                os.path.getsize(self.log_file) > self.max_size_bytes):
                self._rotate_logs()
        except Exception as e:
            print(f"❌ Ошибка ротации логов: {e}")

    def _rotate_logs(self):
        """Выполняет ротацию лог-файлов."""
        # Сдвигаем существующие архивы
        for version in range(self.archive_limit-1, 0, -1):
            current_archive = f"{self.log_file}.{version}.gz"
            next_archive = f"{self.log_file}.{version+1}.gz"
            if os.path.exists(current_archive):
                os.rename(current_archive, next_archive)

        # Создаем новый архив
        new_archive = f"{self.log_file}.1.gz"
        
        try:
            # Архивируем текущие данные
            with open(self.log_file, 'rb') as source:
                with gzip.open(new_archive, 'wb') as dest:
                    dest.writelines(source)
            
            # Очищаем основной файл
            with open(self.log_file, 'w') as f:
                f.write("")
            self.events.clear()
            
            print(f"🔄 Логи заархивированы: {new_archive}")
            
        except Exception as e:
            print(f"❌ Ошибка архивации: {e}")

    def _should_exclude_event(self, event_type, event_data):
        """Определяет, нужно ли исключить событие."""
        try:
            if event_type in ["process_start", "process_end"]:
                process_name = event_data.get('name', '').lower()
                return any(excluded in process_name for excluded in EXCLUDED_PROCESSES)
            
            elif event_type.startswith("file_"):
                file_path = event_data.get('path', '')
                full_path = os.path.abspath(file_path) if file_path else ''
                return any(pattern in full_path for pattern in EXCLUDED_PATTERNS)
            
            return False
        except Exception:
            return False

    def _get_timestamp(self):
        """Безопасное получение временной метки."""
        try:
            return datetime.now().isoformat()
        except Exception:
            import time
            return str(time.time())

    def log_event(self, event_type, event_data):
        """Основной метод для логирования событий."""
        # Проверяем ротацию
        self._check_size_and_rotate()
        
        # Проверяем исключения
        if self._should_exclude_event(event_type, event_data):
            return

        # Создаем запись события
        event_record = {
            "timestamp": self._get_timestamp(), 
            "type": event_type,
            "data": event_data
        }
        
        # Сохраняем в память и файл
        self.events.append(event_record)
        self._save_event(event_record)
        
        # Отправляем в мессенджер (если доступен)
        try:
            global_messenger.send_message(event_type, event_data)
        except Exception as e:
            print(f"⚠️ Ошибка отправки в мессенджер: {e}")

    def _save_event(self, event_record):
        """Сохраняет событие в файл."""
        try:
            with open(self.log_file, "a", encoding='utf-8') as f:
                f.write(json.dumps(event_record, ensure_ascii=False) + "\n")
        except Exception as e:
            print(f"❌ Ошибка записи события: {e}")

    def search_events(self, filters):
        """Поиск событий по фильтрам."""
        if not filters:
            return self.events.copy()
        
        results = []
        for event in self.events:
            if self._matches_filters(event, filters):
                results.append(event)
        
        # Сортируем по времени (новые сверху)
        results.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        return results

    def _matches_filters(self, event, filters):
        """Проверяет соответствие события фильтрам."""
        for key, value in filters.items():
            if key == "type":
                if event.get("type") != value:
                    return False
            elif key == "pid":
                event_pid = event.get("data", {}).get("pid")
                if event_pid != value:
                    return False
            elif key == "name":
                event_name = event.get("data", {}).get("name", "").lower()
                if value.lower() not in event_name:
                    return False
            elif key == "path":
                event_path = event.get("data", {}).get("path", "").lower()
                if value.lower() not in event_path:
                    return False
        return True

    def clear_events(self):
        """Очищает все события."""
        try:
            self.events.clear()
            if os.path.exists(self.log_file):
                os.remove(self.log_file)
            print("🗑️ Все события очищены")
        except Exception as e:
            print(f"❌ Ошибка очистки событий: {e}")

    def get_statistics(self):
        """Возвращает статистику по событиям."""
        stats = {
            'total': len(self.events),
            'process_start': 0,
            'process_end': 0,
            'file_created': 0,
            'file_modified': 0,
            'file_deleted': 0,
            'network_connection': 0,
            'system': 0
        }
        
        for event in self.events:
            event_type = event.get('type', '')
            if event_type in stats:
                stats[event_type] += 1
            elif event_type.startswith('file_'):
                stats['file_events'] = stats.get('file_events', 0) + 1
        
        return stats

    def get_recent_events(self, count=50):
        """Возвращает последние N событий."""
        return self.events[-count:] if self.events else []

    def export_events(self, output_file=None):
        """Экспортирует события в файл."""
        if not output_file:
            timestamp = self._get_timestamp().replace(':', '-').split('.')[0]
            output_file = f"audit_export_{timestamp}.json"
        
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(self.events, f, ensure_ascii=False, indent=2)
            return output_file
        except Exception as e:
            print(f"❌ Ошибка экспорта: {e}")
            return None

# Создаем глобальный экземпляр для импорта
event_logger = EventLogger()

# Для обратной совместимости можно оставить старый класс
ActivityRecorder = EventLogger