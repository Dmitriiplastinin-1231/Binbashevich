# Дополнительные исключения для реального мониторинга
EXCLUDED_PATTERNS = [
    # Системные файлы мониторинга
    'event_log.json',
    'messages_storage.json',
    'internal_messages.json',
    'reports/',
    '__pycache__/',
    '.pyc',
    '.log',
    
    # Временные файлы
    '.tmp',
    '.temp',
    '~',
    
    # Служебные файлы системы
    '.git/',
    '.vscode/',
    '.idea/',
    
    # Системные директории Linux
    '/proc/',
    '/sys/',
    '/dev/',
    '/run/',
    '/tmp/'
]

EXCLUDED_PROCESSES = [
    'python',
    'python3',
    'interface.py',
    'notifier.py',
    'systemd',
    'kthreadd',
    'ksoftirqd'
]

SECURITY_CONFIG = {
    'run_as_user': 'nobody',
    'allowed_directories': ['/tmp', '/home/user/audit_logs'],
    'max_file_size_mb': 50,
    'chroot_directory': None
}

LOG_MAX_SIZE_MB = 10
LOG_BACKUP_COUNT = 5