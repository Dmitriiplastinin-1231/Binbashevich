import json
import os
import time
from datetime import datetime
from collections import deque

class InternalMessenger:
    def __init__(self, storage_file="messages_storage.json"):
        self.storage_file = storage_file
        self._load_messages()
    
    def _load_messages(self):
        try:
            if os.path.exists(self.storage_file):
                with open(self.storage_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.messages = deque(data.get('messages', []), maxlen=100)
                    self.next_id = data.get('next_id', 1)
                    print(f"📂 Загружено {len(self.messages)} сообщений из файла")
            else:
                self.messages = deque(maxlen=100)
                self.next_id = 1
                print("🆕 Создано новое хранилище сообщений")
        except Exception as e:
            print(f"❌ Ошибка загрузки сообщений: {e}")
            self.messages = deque(maxlen=100)
            self.next_id = 1
    
    def _save_messages(self):
        try:
            data = {
                'messages': list(self.messages),
                'next_id': self.next_id,
                'last_save': datetime.now().isoformat()
            }
            with open(self.storage_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"❌ Ошибка сохранения сообщений: {e}")
    
    def send_message(self, event_type, event_data):
        message = {
            'id': self.next_id,
            'timestamp': datetime.now().isoformat(),
            'type': event_type,
            'data': event_data,
            'read': False
        }
        
        self.next_id += 1
        self.messages.appendleft(message)
        self._save_messages()
        
        print(f"📨 Сообщение {message['id']}: {event_type} (всего: {len(self.messages)})")
        return message
    
    def get_all_messages(self):
        self._load_messages()
        print(f"📂 Возвращаем {len(self.messages)} сообщений")
        return list(self.messages)
    
    def get_new_messages(self, last_seen_id=0):
        self._load_messages()
        new_msgs = [msg for msg in self.messages if msg['id'] > last_seen_id]
        return new_msgs
    
    def get_unread_messages(self):
        self._load_messages()
        return [msg for msg in self.messages if not msg['read']]
    
    def mark_as_read(self, message_id=None):
        self._load_messages()
        
        if message_id:
            for msg in self.messages:
                if msg['id'] == message_id:
                    msg['read'] = True
        else:
            for msg in self.messages:
                msg['read'] = True
        
        self._save_messages()
    
    def get_stats(self):
        self._load_messages()
        total = len(self.messages)
        unread = len(self.get_unread_messages())
        
        return {
            'total_messages': total,
            'unread_messages': unread,
            'last_message_id': self.messages[0]['id'] if self.messages else 0
        }

global_messenger = InternalMessenger()