"""
Модуль анализа сетевого трафика.
Определяет подозрительные активности на основе правил.
"""

from scapy.all import IP, TCP, UDP, ICMP
from datetime import datetime
from collections import defaultdict
import time


class TrafficAnalyzer:
    """Класс для анализа сетевого трафика и обнаружения аномалий."""
    
    def __init__(self):
        self.suspicious_ips = set()
        self.port_scan_attempts = defaultdict(set)
        self.connection_count = defaultdict(int)
        self.packet_sizes = defaultdict(list)
        self.last_reset = time.time()
        
        # Настройки правил обнаружения
        self.MAX_PACKET_SIZE = 10000  # Максимальный размер пакета в байтах
        self.PORT_SCAN_THRESHOLD = 10  # Количество портов для определения сканирования
        self.CONNECTION_THRESHOLD = 50  # Максимальное количество соединений в минуту
        self.RESET_INTERVAL = 60  # Интервал сброса счетчиков (секунды)
        
    def reset_counters(self):
        """Сбрасывает счетчики по истечении интервала."""
        current_time = time.time()
        if current_time - self.last_reset > self.RESET_INTERVAL:
            self.port_scan_attempts.clear()
            self.connection_count.clear()
            self.packet_sizes.clear()
            self.last_reset = current_time
    
    def analyze_packet(self, packet):
        """
        Анализирует пакет и определяет, является ли он подозрительным.
        
        Args:
            packet: Пакет Scapy для анализа
            
        Returns:
            tuple: (is_suspicious, reason, details)
        """
        self.reset_counters()
        
        if not packet.haslayer(IP):
            return False, None, None
        
        src_ip = packet[IP].src
        dst_ip = packet[IP].dst
        packet_size = len(packet)
        
        # Проверка размера пакета
        if packet_size > self.MAX_PACKET_SIZE:
            return True, "Аномально большой пакет", {
                "src_ip": src_ip,
                "dst_ip": dst_ip,
                "size": packet_size,
                "timestamp": datetime.now().isoformat()
            }
        
        # Проверка сканирования портов
        if packet.haslayer(TCP):
            dst_port = packet[TCP].dport
            self.port_scan_attempts[src_ip].add(dst_port)
            
            if len(self.port_scan_attempts[src_ip]) > self.PORT_SCAN_THRESHOLD:
                return True, "Обнаружено сканирование портов", {
                    "src_ip": src_ip,
                    "scanned_ports": len(self.port_scan_attempts[src_ip]),
                    "timestamp": datetime.now().isoformat()
                }
        
        # Проверка количества соединений
        self.connection_count[src_ip] += 1
        if self.connection_count[src_ip] > self.CONNECTION_THRESHOLD:
            return True, "Превышен лимит соединений", {
                "src_ip": src_ip,
                "connections": self.connection_count[src_ip],
                "timestamp": datetime.now().isoformat()
            }
        
        # Проверка SYN flood атаки
        if packet.haslayer(TCP):
            if packet[TCP].flags == "S":  # SYN флаг
                self.connection_count[f"{src_ip}_syn"] += 1
                if self.connection_count[f"{src_ip}_syn"] > 30:
                    return True, "Возможная SYN flood атака", {
                        "src_ip": src_ip,
                        "syn_packets": self.connection_count[f"{src_ip}_syn"],
                        "timestamp": datetime.now().isoformat()
                    }
        
        # Проверка ICMP flood
        if packet.haslayer(ICMP):
            self.connection_count[f"{src_ip}_icmp"] += 1
            if self.connection_count[f"{src_ip}_icmp"] > 40:
                return True, "Возможная ICMP flood атака", {
                    "src_ip": src_ip,
                    "icmp_packets": self.connection_count[f"{src_ip}_icmp"],
                    "timestamp": datetime.now().isoformat()
                }
        
        # Проверка UDP flood
        if packet.haslayer(UDP):
            self.connection_count[f"{src_ip}_udp"] += 1
            if self.connection_count[f"{src_ip}_udp"] > 50:
                return True, "Возможная UDP flood атака", {
                    "src_ip": src_ip,
                    "udp_packets": self.connection_count[f"{src_ip}_udp"],
                    "timestamp": datetime.now().isoformat()
                }
        
        return False, None, None
    
    def get_packet_info(self, packet):
        """
        Извлекает информацию из пакета.
        
        Args:
            packet: Пакет Scapy
            
        Returns:
            dict: Информация о пакете
        """
        info = {
            "timestamp": datetime.now().isoformat(),
            "size": len(packet)
        }
        
        if packet.haslayer(IP):
            info["src_ip"] = packet[IP].src
            info["dst_ip"] = packet[IP].dst
            info["protocol"] = packet[IP].proto
            
        if packet.haslayer(TCP):
            info["src_port"] = packet[TCP].sport
            info["dst_port"] = packet[TCP].dport
            info["flags"] = str(packet[TCP].flags)
            info["protocol_name"] = "TCP"
            
        elif packet.haslayer(UDP):
            info["src_port"] = packet[UDP].sport
            info["dst_port"] = packet[UDP].dport
            info["protocol_name"] = "UDP"
            
        elif packet.haslayer(ICMP):
            info["icmp_type"] = packet[ICMP].type
            info["protocol_name"] = "ICMP"
        
        return info
    
    def add_to_blocklist(self, ip):
        """Добавляет IP в список блокировки."""
        self.suspicious_ips.add(ip)
    
    def remove_from_blocklist(self, ip):
        """Удаляет IP из списка блокировки."""
        self.suspicious_ips.discard(ip)
    
    def is_blocked(self, ip):
        """Проверяет, заблокирован ли IP."""
        return ip in self.suspicious_ips
    
    def get_statistics(self):
        """Возвращает статистику анализа."""
        return {
            "blocked_ips": len(self.suspicious_ips),
            "monitored_ips": len(self.connection_count),
            "port_scan_suspects": len(self.port_scan_attempts),
            "total_connections": sum(self.connection_count.values())
        }
