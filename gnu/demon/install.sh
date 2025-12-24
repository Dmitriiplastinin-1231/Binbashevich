#!/bin/bash

# Скрипт установки демона резервного копирования

CONFIG_DIR="/etc/backup_daemon"
SERVICE_DIR="/etc/systemd/system"
SCRIPT_DIR="/usr/local/bin"

echo "Installing Backup Daemon..."

# Создание директорий
sudo mkdir -p $CONFIG_DIR
sudo mkdir -p /var/log/backup_daemon

# Копирование файлов
sudo cp backup_daemon.py $SCRIPT_DIR/
sudo cp backup_service.py $SCRIPT_DIR/
sudo cp backup_config.ini $CONFIG_DIR/config.ini

# Установка прав
sudo chmod 755 $SCRIPT_DIR/backup_daemon.py
sudo chmod 755 $SCRIPT_DIR/backup_service.py
sudo chmod 640 $CONFIG_DIR/config.ini

# Создание systemd service файла
sudo tee $SERVICE_DIR/backup-daemon.service > /dev/null << EOF
[Unit]
Description=Backup Daemon Service
After=network.target

[Service]
Type=simple
User=root
ExecStart=/usr/bin/python3 $SCRIPT_DIR/backup_daemon.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

# Перезагрузка systemd
sudo systemctl daemon-reload

echo "Installation completed!"
echo "Edit configuration: $CONFIG_DIR/config.ini"
echo "Start service: sudo systemctl start backup-daemon"
echo "Enable autostart: sudo systemctl enable backup-daemon"