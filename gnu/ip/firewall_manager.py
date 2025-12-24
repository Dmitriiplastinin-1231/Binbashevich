"""
Модуль управления блокировкой трафика.
Использует iptables для блокировки подозрительных IP-адресов.
"""

import subprocess
import logging
from datetime import datetime


class FirewallManager:
    """Класс для управления правилами файрвола."""
    
    def __init__(self):
        self.blocked_ips = {}
        self.logger = logging.getLogger(__name__)
        
    def block_ip(self, ip_address, reason="Подозрительная активность"):
        """
        Блокирует IP-адрес с помощью iptables.
        
        Args:
            ip_address: IP-адрес для блокировки
            reason: Причина блокировки
            
        Returns:
            bool: True если блокировка успешна
        """
        if ip_address in self.blocked_ips:
            self.logger.info(f"IP {ip_address} уже заблокирован")
            return False
        
        try:
            # Попытка добавить правило iptables (требует sudo)
            # В реальной системе нужны права root
            command = f"sudo iptables -A INPUT -s {ip_address} -j DROP"
            
            # Симуляция блокировки (для тестирования без прав root)
            self.logger.info(f"Попытка блокировки IP: {ip_address}")
            self.logger.info(f"Команда: {command}")
            
            # Раскомментируйте для реальной блокировки:
            # result = subprocess.run(
            #     command.split(),
            #     capture_output=True,
            #     text=True,
            #     timeout=5
            # )
            # 
            # if result.returncode != 0:
            #     self.logger.error(f"Ошибка блокировки: {result.stderr}")
            #     return False
            
            self.blocked_ips[ip_address] = {
                "timestamp": datetime.now().isoformat(),
                "reason": reason
            }
            
            self.logger.info(f"IP {ip_address} заблокирован: {reason}")
            return True
            
        except Exception as e:
            self.logger.error(f"Ошибка при блокировке IP {ip_address}: {e}")
            return False
    
    def unblock_ip(self, ip_address):
        """
        Разблокирует IP-адрес.
        
        Args:
            ip_address: IP-адрес для разблокировки
            
        Returns:
            bool: True если разблокировка успешна
        """
        if ip_address not in self.blocked_ips:
            self.logger.info(f"IP {ip_address} не был заблокирован")
            return False
        
        try:
            # Попытка удалить правило iptables
            command = f"sudo iptables -D INPUT -s {ip_address} -j DROP"
            
            # Симуляция разблокировки
            self.logger.info(f"Попытка разблокировки IP: {ip_address}")
            self.logger.info(f"Команда: {command}")
            
            # Раскомментируйте для реальной разблокировки:
            # result = subprocess.run(
            #     command.split(),
            #     capture_output=True,
            #     text=True,
            #     timeout=5
            # )
            # 
            # if result.returncode != 0:
            #     self.logger.error(f"Ошибка разблокировки: {result.stderr}")
            #     return False
            
            del self.blocked_ips[ip_address]
            self.logger.info(f"IP {ip_address} разблокирован")
            return True
            
        except Exception as e:
            self.logger.error(f"Ошибка при разблокировке IP {ip_address}: {e}")
            return False
    
    def is_blocked(self, ip_address):
        """Проверяет, заблокирован ли IP."""
        return ip_address in self.blocked_ips
    
    def get_blocked_list(self):
        """Возвращает список заблокированных IP."""
        return self.blocked_ips.copy()
    
    def clear_all_blocks(self):
        """Удаляет все блокировки."""
        blocked_list = list(self.blocked_ips.keys())
        for ip in blocked_list:
            self.unblock_ip(ip)
        
        self.logger.info("Все блокировки сняты")
    
    def send_icmp_unreachable(self, target_ip):
        """
        Отправляет ICMP сообщение о недостижимости.
        
        Args:
            target_ip: IP-адрес получателя
        """
        try:
            from scapy.all import IP, ICMP, send
            
            packet = IP(dst=target_ip) / ICMP(type=3, code=13)
            
            # Симуляция отправки
            self.logger.info(f"Отправка ICMP Unreachable на {target_ip}")
            
            # Раскомментируйте для реальной отправки:
            # send(packet, verbose=0)
            
        except Exception as e:
            self.logger.error(f"Ошибка отправки ICMP: {e}")
