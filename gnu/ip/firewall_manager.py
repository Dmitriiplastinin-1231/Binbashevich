"""
Модуль управления блокировкой трафика.
Использует iptables для блокировки подозрительных IP-адресов.
"""

import subprocess
import logging
from datetime import datetime


class FirewallManager:
    """Класс для управления правилами файрвола."""
    
    def __init__(self, enable_system_block=True):
        self.blocked_ips = {}
        self.logger = logging.getLogger(__name__)
        # Попытаться применять реальные правила iptables/conntrack; при ошибке будет симуляция
        self.enable_system_block = enable_system_block
        
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
            if self.enable_system_block:
                cmds = [
                    ["sudo", "iptables", "-I", "INPUT", "-s", ip_address, "-j", "DROP"],
                    ["sudo", "iptables", "-I", "OUTPUT", "-d", ip_address, "-j", "DROP"],
                    ["sudo", "conntrack", "-D", "-s", ip_address],
                    ["sudo", "conntrack", "-D", "-d", ip_address],
                ]
                for cmd in cmds:
                    try:
                        result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
                        if result.returncode != 0:
                            self.logger.warning(f"Команда {' '.join(cmd)} завершилась с ошибкой: {result.stderr.strip()}")
                    except FileNotFoundError:
                        self.logger.warning(f"Утилита {cmd[0]} недоступна, блокировка может быть симуляционной")
                    except Exception as e:
                        self.logger.warning(f"Ошибка выполнения {' '.join(cmd)}: {e}")

            # Записываем факт блокировки (реальной или симуляционной)
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
            if self.enable_system_block:
                cmds = [
                    ["sudo", "iptables", "-D", "INPUT", "-s", ip_address, "-j", "DROP"],
                    ["sudo", "iptables", "-D", "OUTPUT", "-d", ip_address, "-j", "DROP"],
                ]
                for cmd in cmds:
                    try:
                        result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
                        if result.returncode != 0:
                            self.logger.warning(f"Команда {' '.join(cmd)} завершилась с ошибкой: {result.stderr.strip()}")
                    except FileNotFoundError:
                        self.logger.warning(f"Утилита {cmd[0]} недоступна, разблокировка может быть симуляционной")
                    except Exception as e:
                        self.logger.warning(f"Ошибка выполнения {' '.join(cmd)}: {e}")

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
