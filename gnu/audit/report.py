import json
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
import os
from collections import Counter

class ReportGenerator:
    """Генератор отчетов на основе логов событий."""
    
    def __init__(self, log_file="event_log.json"):
        self.log_file = log_file
        self.output_dir = "reports"
        os.makedirs(self.output_dir, exist_ok=True)
    
    def load_events(self):
        """Загружает события из лог-файла."""
        events = []
        try:
            with open(self.log_file, "r", encoding='utf-8') as f:
                for line in f:
                    try:
                        events.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
        except FileNotFoundError:
            print(f"Файл логов {self.log_file} не найден")
        return events
    
    def generate_statistics(self, events):
        """Генерирует статистику по событиям."""
        if not events:
            return {}
        
        df = pd.DataFrame(events)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df['date'] = df['timestamp'].dt.date
        df['hour'] = df['timestamp'].dt.hour
        
        stats = {
            'total_events': len(events),
            'time_period': {
                'start': df['timestamp'].min().strftime('%Y-%m-%d %H:%M:%S'),
                'end': df['timestamp'].max().strftime('%Y-%m-%d %H:%M:%S'),
                'duration_days': (df['timestamp'].max() - df['timestamp'].min()).days
            },
            'event_types': df['type'].value_counts().to_dict(),
            'top_processes': self._get_top_processes(df),
            'top_files': self._get_top_files(df),
            'network_stats': self._get_network_stats(df),
            'hourly_activity': df['hour'].value_counts().sort_index().to_dict(),
            'daily_activity': df['date'].value_counts().sort_index().to_dict()
        }
        
        return stats
    
    def _get_top_processes(self, df):
        """Возвращает статистику по процессам."""
        process_starts = df[df['type'] == 'process_start']
        if process_starts.empty:
            return {}
        
        process_names = process_starts['data'].apply(lambda x: x.get('name', 'Unknown'))
        return process_names.value_counts().head(10).to_dict()
    
    def _get_top_files(self, df):
        """Возвращает статистику по файлам."""
        file_events = df[df['type'].str.contains('file_')]
        if file_events.empty:
            return {}
        
        file_paths = file_events['data'].apply(lambda x: x.get('path', 'Unknown'))
        return file_paths.value_counts().head(10).to_dict()
    
    def _get_network_stats(self, df):
        """Возвращает статистику по сети."""
        network_events = df[df['type'] == 'network_connection']
        if network_events.empty:
            return {}
        
        connection_types = network_events['data'].apply(lambda x: x.get('type', 'Unknown'))
        local_addresses = network_events['data'].apply(lambda x: x.get('local_address', 'Unknown'))
        
        return {
            'total_connections': len(network_events),
            'connection_types': connection_types.value_counts().to_dict(),
            'top_local_addresses': local_addresses.value_counts().head(5).to_dict()
        }
    
    def create_plots(self, events, report_id):
        """Создает графики для отчета."""
        if not events:
            return []
        
        df = pd.DataFrame(events)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        plots = []
        
        # 1. Распределение типов событий
        plt.figure(figsize=(10, 6))
        event_counts = df['type'].value_counts()
        plt.pie(event_counts.values, labels=event_counts.index, autopct='%1.1f%%', startangle=90)
        plt.title('Распределение типов событий')
        plot_path = f"{self.output_dir}/event_types_{report_id}.png"
        plt.savefig(plot_path, bbox_inches='tight', dpi=150)
        plt.close()
        plots.append(plot_path)
        
        # 2. Активность по часам
        plt.figure(figsize=(12, 6))
        hourly_counts = df['timestamp'].dt.hour.value_counts().sort_index()
        plt.plot(hourly_counts.index, hourly_counts.values, marker='o', linewidth=2)
        plt.title('Активность системы по часам')
        plt.xlabel('Час дня')
        plt.ylabel('Количество событий')
        plt.grid(True, alpha=0.3)
        plot_path = f"{self.output_dir}/hourly_activity_{report_id}.png"
        plt.savefig(plot_path, bbox_inches='tight', dpi=150)
        plt.close()
        plots.append(plot_path)
        
        # 3. Топ процессов
        process_starts = df[df['type'] == 'process_start']
        if not process_starts.empty:
            plt.figure(figsize=(12, 6))
            top_processes = process_starts['data'].apply(
                lambda x: x.get('name', 'Unknown')
            ).value_counts().head(10)
            
            plt.barh(range(len(top_processes)), top_processes.values)
            plt.yticks(range(len(top_processes)), top_processes.index)
            plt.title('Топ-10 процессов по количеству запусков')
            plt.xlabel('Количество запусков')
            plt.gca().invert_yaxis()
            plot_path = f"{self.output_dir}/top_processes_{report_id}.png"
            plt.savefig(plot_path, bbox_inches='tight', dpi=150)
            plt.close()
            plots.append(plot_path)
        
        # 4. Топ файлов
        file_events = df[df['type'].str.contains('file_')]
        if not file_events.empty:
            plt.figure(figsize=(12, 6))
            top_files = file_events['data'].apply(
                lambda x: x.get('path', 'Unknown')
            ).value_counts().head(10)
            
            plt.barh(range(len(top_files)), top_files.values)
            plt.yticks(range(len(top_files)), [os.path.basename(path) for path in top_files.index])
            plt.title('Топ-10 файлов по количеству изменений')
            plt.xlabel('Количество изменений')
            plt.gca().invert_yaxis()
            plot_path = f"{self.output_dir}/top_files_{report_id}.png"
            plt.savefig(plot_path, bbox_inches='tight', dpi=150)
            plt.close()
            plots.append(plot_path)
        
        return plots
    
    def generate_markdown_report(self, stats, plots, report_id):
        """Генерирует Markdown отчет."""
        report_file = f"{self.output_dir}/system_report_{report_id}.md"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            # Заголовок
            f.write("# Отчет аудита системы\n\n")
            f.write(f"**Дата генерации:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            # Общая статистика
            f.write("## 📊 Общая статистика\n\n")
            f.write(f"- **Всего событий:** {stats['total_events']}\n")
            f.write(f"- **Период мониторинга:** с {stats['time_period']['start']} по {stats['time_period']['end']}\n")
            f.write(f"- **Длительность:** {stats['time_period']['duration_days']} дней\n\n")
            
            # Распределение по типам событий
            f.write("## 📈 Распределение по типам событий\n\n")
            for event_type, count in stats['event_types'].items():
                percentage = (count / stats['total_events']) * 100
                f.write(f"- **{event_type}:** {count} событий ({percentage:.1f}%)\n")
            f.write("\n")
            
            # Топ процессов
            if stats['top_processes']:
                f.write("## 🔥 Топ процессов\n\n")
                for process, count in stats['top_processes'].items():
                    f.write(f"- **{process}:** {count} запусков\n")
                f.write("\n")
            
            # Топ файлов
            if stats['top_files']:
                f.write("## 📁 Топ файлов\n\n")
                for file_path, count in stats['top_files'].items():
                    f.write(f"- **{os.path.basename(file_path)}** ({file_path}): {count} изменений\n")
                f.write("\n")
            
            # Сетевая активность
            if stats['network_stats']:
                f.write("## 🌐 Сетевая активность\n\n")
                f.write(f"- **Всего подключений:** {stats['network_stats']['total_connections']}\n")
                for conn_type, count in stats['network_stats']['connection_types'].items():
                    f.write(f"- **{conn_type} подключений:** {count}\n")
                f.write("\n")
            
            # Графики
            f.write("## 📊 Визуализация\n\n")
            for plot_path in plots:
                plot_name = os.path.basename(plot_path)
                f.write(f"### {self._get_plot_title(plot_name)}\n\n")
                f.write(f"![{plot_name}]({plot_name})\n\n")
            
            # Заключение
            f.write("## 💡 Заключение\n\n")
            f.write("Отчет сгенерирован автоматически системой мониторинга.\n")
            f.write(f"Всего зафиксировано **{stats['total_events']}** системных событий.\n")
        
        return report_file
    
    def _get_plot_title(self, plot_name):
        """Возвращает заголовок для графика."""
        titles = {
            'event_types': 'Распределение типов событий',
            'hourly_activity': 'Активность по часам',
            'top_processes': 'Топ процессов',
            'top_files': 'Топ файлов'
        }
        
        for key, title in titles.items():
            if key in plot_name:
                return title
        return "График"
    
    def generate_report(self, report_id=None):
        """Генерирует полный отчет."""
        if report_id is None:
            report_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        print(f"📊 Генерация отчета {report_id}...")
        
        # Загрузка событий
        events = self.load_events()
        
        if not events:
            print("❌ Нет данных для генерации отчета")
            return None
        
        # Генерация статистики
        stats = self.generate_statistics(events)
        
        # Создание графиков
        plots = self.create_plots(events, report_id)
        
        # Генерация Markdown отчета
        report_file = self.generate_markdown_report(stats, plots, report_id)
        
        print(f"✅ Отчет сохранен: {report_file}")
        print(f"📈 Создано графиков: {len(plots)}")
        print(f"📝 Всего событий в отчете: {stats['total_events']}")
        
        return report_file

def main():
    """Основная функция для запуска из командной строки."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Генератор отчетов системы мониторинга')
    parser.add_argument('--log-file', default='event_log.json', help='Файл с логами событий')
    parser.add_argument('--report-id', help='ID отчета (по умолчанию: текущее время)')
    
    args = parser.parse_args()
    
    generator = ReportGenerator(args.log_file)
    report_file = generator.generate_report(args.report_id)
    
    if report_file:
        print(f"\n🎉 Отчет успешно создан: {report_file}")
    else:
        print("\n❌ Не удалось создать отчет")

if __name__ == "__main__":
    main()