"""
Модуль мониторинга сетевого трафика.
Захватывает и анализирует сетевые пакеты в реальном времени.
"""

from scapy.all import sniff, conf
import threading
import logging
from queue import Queue


class TrafficMonitor:
    """Класс для мониторинга сетевого трафика."""
    
    def __init__(self, analyzer, firewall, callback=None):
        """
        Инициализация монитора трафика.
        
        Args:
            analyzer: Экземпляр TrafficAnalyzer
            firewall: Экземпляр FirewallManager
            callback: Функция обратного вызова для обновления GUI
        """
        self.analyzer = analyzer
        self.firewall = firewall
        self.callback = callback
        self.is_running = False
        self.packet_queue = Queue()
        self.logger = logging.getLogger(__name__)
        self.thread = None
        self.packet_count = 0
        self.suspicious_count = 0
        
    def start_monitoring(self, interface=None, filter_str=None):
        """
        Запускает мониторинг трафика.
        
        Args:
            interface: Сетевой интерфейс для мониторинга (None = все)
            filter_str: BPF фильтр для фильтрации пакетов
        """
        if self.is_running:
            self.logger.warning("Мониторинг уже запущен")
            return
        
        self.is_running = True
        self.thread = threading.Thread(
            target=self._monitor_loop,
            args=(interface, filter_str),
            daemon=True
        )
        self.thread.start()
        self.logger.info("Мониторинг трафика запущен")
        
    def stop_monitoring(self):
        """Останавливает мониторинг трафика."""
        self.is_running = False
        if self.thread:
            self.thread.join(timeout=2)
        self.logger.info("Мониторинг трафика остановлен")
    
    def _monitor_loop(self, interface, filter_str):
        """Основной цикл мониторинга."""
        try:
            # Отключаем вывод Scapy
            conf.verb = 0
            
            # Запускаем захват пакетов
            sniff(
                iface=interface,
                filter=filter_str,
                prn=self._process_packet,
                store=False,
                stop_filter=lambda x: not self.is_running
            )
        except Exception as e:
            self.logger.error(f"Ошибка мониторинга: {e}")
            self.is_running = False
    
    def _process_packet(self, packet):
        """
        Обрабатывает захваченный пакет.
        
        Args:
            packet: Захваченный пакет Scapy
        """
        try:
            self.packet_count += 1
            
            # Получаем информацию о пакете
            packet_info = self.analyzer.get_packet_info(packet)
            
            # Анализируем пакет на подозрительность
            is_suspicious, reason, details = self.analyzer.analyze_packet(packet)
            
            if is_suspicious:
                self.suspicious_count += 1
                src_ip = details.get("src_ip")
                
                # Блокируем IP
                if src_ip and not self.firewall.is_blocked(src_ip):
                    self.firewall.block_ip(src_ip, reason)
                    self.analyzer.add_to_blocklist(src_ip)
                    
                    # Отправляем ICMP unreachable
                    self.firewall.send_icmp_unreachable(src_ip)
                
                # Уведомляем GUI
                if self.callback:
                    self.callback("suspicious", {
                        "packet_info": packet_info,
                        "reason": reason,
                        "details": details
                    })
            else:
                # Обычный пакет
                if self.callback and self.packet_count % 100 == 0:  # Обновляем каждые 100 пакетов
                    self.callback("normal", {
                        "packet_info": packet_info,
                        "total_packets": self.packet_count,
                        "suspicious_packets": self.suspicious_count
                    })
                    
        except Exception as e:
            self.logger.error(f"Ошибка обработки пакета: {e}")
    
    def get_statistics(self):
        """Возвращает статистику мониторинга."""
        return {
            "total_packets": self.packet_count,
            "suspicious_packets": self.suspicious_count,
            "is_running": self.is_running,
            "blocked_ips": len(self.firewall.get_blocked_list())
        }
    
    def reset_statistics(self):
        """Сбрасывает статистику."""
        self.packet_count = 0
        self.suspicious_count = 0
