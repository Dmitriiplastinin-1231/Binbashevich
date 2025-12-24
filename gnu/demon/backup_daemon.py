#!/usr/bin/env python3
import os
import sys
import time
import shutil
import logging
import configparser
import datetime
import signal
import daemon
import daemon.pidfile
from pathlib import Path

class BackupDaemon:
    def __init__(self, config_file='/etc/backup_daemon/config.ini'):
        self.config_file = config_file
        self.running = False
        self.load_config()
        self.setup_logging()
        
    def load_config(self):
        """Загрузка конфигурации"""
        self.config = configparser.ConfigParser()
        
        if not os.path.exists(self.config_file):
            raise FileNotFoundError(f"Config file {self.config_file} not found")
            
        self.config.read(self.config_file)
        
        # Основные настройки
        self.source_dir = self.config['Backup'].get('source_dir')
        self.backup_dir = self.config['Backup'].get('backup_dir')
        self.interval = int(self.config['Backup'].get('interval_minutes', 60))
        self.max_backups = int(self.config['Backup'].get('max_backups', 30))
        self.compress = self.config['Backup'].getboolean('compress', True)
        
        # Проверка директорий
        if not os.path.exists(self.source_dir):
            raise FileNotFoundError(f"Source directory {self.source_dir} not found")
            
        if not os.path.exists(self.backup_dir):
            os.makedirs(self.backup_dir, exist_ok=True)
    
    def setup_logging(self):
        """Настройка логирования только в файл"""
        log_file = self.config['Logging'].get('log_file', '/var/log/backup_daemon.log')
        log_level = getattr(logging, self.config['Logging'].get('log_level', 'INFO'))
        
        # Создаем директорию для логов если не существует
        log_dir = os.path.dirname(log_file)
        if not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)
            
        # Очищаем существующие обработчики
        logging.getLogger().handlers.clear()
            
        # Настраиваем логирование только в файл
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
            ]
        )
        self.logger = logging.getLogger('BackupDaemon')
    
    def create_backup(self):
        """Создание резервной копии"""
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_name = f"backup_{timestamp}"
        backup_path = os.path.join(self.backup_dir, backup_name)
        
        try:
            self.logger.info(f"Starting backup: {backup_name}")
            
            if self.compress:
                # Создаем архив
                shutil.make_archive(backup_path, 'zip', self.source_dir)
                backup_path += '.zip'
                self.logger.info(f"Compressed backup created: {backup_path}")
            else:
                # Копируем файлы
                shutil.copytree(self.source_dir, backup_path)
                self.logger.info(f"Directory backup created: {backup_path}")
            
            self.cleanup_old_backups()
            
        except Exception as e:
            self.logger.error(f"Backup failed: {str(e)}")
    
    def cleanup_old_backups(self):
        """Удаление старых резервных копий"""
        try:
            backups = []
            for item in os.listdir(self.backup_dir):
                if item.startswith('backup_'):
                    item_path = os.path.join(self.backup_dir, item)
                    backups.append((os.path.getmtime(item_path), item_path))
            
            backups.sort(reverse=True)
            
            if len(backups) > self.max_backups:
                for _, old_backup in backups[self.max_backups:]:
                    if os.path.isfile(old_backup):
                        os.remove(old_backup)
                    elif os.path.isdir(old_backup):
                        shutil.rmtree(old_backup)
                    self.logger.info(f"Removed old backup: {old_backup}")
                    
        except Exception as e:
            self.logger.error(f"Cleanup failed: {str(e)}")
    
    def signal_handler(self, signum, frame):
        """Обработчик сигналов"""
        self.logger.info("Received shutdown signal")
        self.running = False
    
    def run_daemon(self):
        """Основной цикл демона в фоновом режиме"""
        self.running = True
        
        # Установка обработчиков сигналов
        signal.signal(signal.SIGTERM, self.signal_handler)
        signal.signal(signal.SIGINT, self.signal_handler)
        
        self.logger.info("Backup daemon started in background mode")
        
        while self.running:
            try:
                self.create_backup()
                
                # Ожидание следующего запуска
                for _ in range(self.interval * 60):
                    if not self.running:
                        break
                    time.sleep(1)
                    
            except Exception as e:
                self.logger.error(f"Error in main loop: {str(e)}")
                time.sleep(60)
        
        self.logger.info("Backup daemon stopped")

def run_as_daemon():
    """Запуск демона в фоновом режиме"""
    try:
        # Создаем экземпляр демона до перехода в фон
        backup_daemon = BackupDaemon()
        
        # Настройка контекста демона
        context = daemon.DaemonContext(
            pidfile=daemon.pidfile.PIDLockFile('/var/run/backup_daemon.pid'),
            signal_map={
                signal.SIGTERM: lambda signum, frame: backup_daemon.signal_handler(signum, frame),
                signal.SIGINT: lambda signum, frame: backup_daemon.signal_handler(signum, frame),
            },
            umask=0o022,
            working_directory='/'
        )
        
        with context:
            backup_daemon.run_daemon()
            
    except Exception as e:
        # Записываем ошибку в системный журнал перед выходом
        with open('/var/log/backup_daemon.log', 'a') as f:
            f.write(f"{datetime.datetime.now()} - ERROR - Failed to start backup daemon: {str(e)}\n")
        sys.exit(1)

def main():
    # Проверяем, запущен ли уже демон
    pid_file = '/var/run/backup_daemon.pid'
    if os.path.exists(pid_file):
        try:
            with open(pid_file, 'r') as f:
                pid = int(f.read().strip())
            # Проверяем, существует ли процесс
            os.kill(pid, 0)
            print("Backup daemon is already running")
            sys.exit(1)
        except (OSError, ValueError):
            # PID файл существует, но процесс не запущен - удаляем файл
            os.remove(pid_file)
    
    # Запускаем демона
    run_as_daemon()

if __name__ == "__main__":
    main()