#!/usr/bin/env python3
import sys
import subprocess
import argparse
import os

def start_daemon():
    """Запуск демона в фоновом режиме"""
    try:
        # Запускаем демона как фоновый процесс
        result = subprocess.run([
            sys.executable, '/usr/local/bin/backup_daemon.py'
        ], check=True)
        print("Backup daemon started in background")
    except subprocess.CalledProcessError as e:
        print(f"Failed to start daemon: {e}")
        sys.exit(1)

def stop_daemon():
    """Остановка демона"""
    try:
        pid_file = '/var/run/backup_daemon.pid'
        if os.path.exists(pid_file):
            with open(pid_file, 'r') as f:
                pid = int(f.read().strip())
            os.kill(pid, 15)  # SIGTERM
            print("Backup daemon stopped")
        else:
            # Альтернативный способ остановки
            result = subprocess.run(['pkill', '-f', 'backup_daemon.py'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                print("Backup daemon stopped")
            else:
                print("Backup daemon is not running")
    except Exception as e:
        print(f"Error stopping daemon: {str(e)}")

def status():
    """Проверка статуса"""
    pid_file = '/var/run/backup_daemon.pid'
    if os.path.exists(pid_file):
        try:
            with open(pid_file, 'r') as f:
                pid = int(f.read().strip())
            os.kill(pid, 0)  # Проверяем существование процесса
            print("Backup daemon is running")
            return True
        except (OSError, ValueError):
            print("Backup daemon is not running (stale PID file)")
            return False
    else:
        # Проверяем через pgrep
        result = subprocess.run(['pgrep', '-f', 'backup_daemon.py'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("Backup daemon is running")
            return True
        else:
            print("Backup daemon is not running")
            return False

def show_logs():
    """Показать последние логи"""
    log_file = '/var/log/backup_daemon.log'
    if os.path.exists(log_file):
        try:
            result = subprocess.run(['tail', '-20', log_file], 
                                  capture_output=True, text=True)
            print("Last 20 log entries:")
            print(result.stdout)
        except Exception as e:
            print(f"Error reading logs: {str(e)}")
    else:
        print("Log file not found")

def main():
    parser = argparse.ArgumentParser(description='Backup Daemon Management')
    parser.add_argument('action', choices=['start', 'stop', 'restart', 'status', 'logs'],
                       help='Action to perform')
    
    args = parser.parse_args()
    
    if args.action == 'start':
        start_daemon()
    elif args.action == 'stop':
        stop_daemon()
    elif args.action == 'restart':
        stop_daemon()
        start_daemon()
    elif args.action == 'status':
        status()
    elif args.action == 'logs':
        show_logs()

if __name__ == "__main__":
    main()