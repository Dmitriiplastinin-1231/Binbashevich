import re
import glob
import matplotlib.pyplot as plt
from datetime import datetime

# Найти все файлы отчетов
report_files = glob.glob("audit_report_*.md")

if not report_files:
    print("Файлы отчетов не найдены!")
    exit()

# Найти самый последний файл по дате в имени
latest_file = None
latest_date = None

for file in report_files:
    match = re.search(r'audit_report_(\d{8})_(\d{6})\.md', file)
    if match:
        date_str = match.group(1) + match.group(2)  # YYYYMMDDHHMMSS
        file_date = datetime.strptime(date_str, "%Y%m%d%H%M%S")
        
        if latest_date is None or file_date > latest_date:
            latest_date = file_date
            latest_file = file

if not latest_file:
    print("Не удалось определить последний отчет!")
    exit()

print(f"Используется отчет: {latest_file}")
print(f"Дата отчета: {latest_date.strftime('%Y-%m-%d %H:%M:%S')}")

# Чтение файла
with open(latest_file, 'r', encoding='utf-8') as f:
    content = f.read()

# Извлечение данных
pattern = r"\*\*([^:]+):\*\* (\d+)"
matches = re.findall(pattern, content)

data = {}
categories = {
    'Запуски процессов': 'Process Starts',
    'Завершения процессов': 'Process Ends', 
    'События файловой системы': 'File System Events',
    'Сетевые соединения': 'Network Connections',
    'Системные события': 'System Events'
}

for match in matches:
    ru_name, value = match
    ru_name = ru_name.strip()
    if ru_name in categories:
        en_name = categories[ru_name]
        data[en_name] = int(value)

# Создание гистограммы
if data:
    plt.figure(figsize=(10, 6))
    bars = plt.bar(data.keys(), data.values(), color=['#3498db', '#e74c3c', '#2ecc71', '#f39c12', '#9b59b6'])
    
    plt.title(f'System Monitoring Statistics\nReport: {latest_file}', fontsize=14, fontweight='bold')
    plt.xlabel('Event Type', fontsize=12)
    plt.ylabel('Count', fontsize=12)
    plt.xticks(rotation=15, fontsize=10)
    plt.grid(axis='y', alpha=0.3, linestyle='--')
    
    # Добавление значений
    for bar, value in zip(bars, data.values()):
        plt.text(bar.get_x() + bar.get_width()/2., bar.get_height() + 0.5,
                str(value), ha='center', va='bottom', fontsize=10)
    
    plt.tight_layout()
    
    # Сохранение
    output_name = f"histogram_{latest_date.strftime('%Y%m%d_%H%M%S')}.png"
    plt.savefig(output_name, dpi=150)
    plt.show()
    
    print(f"\nДанные из отчета:")
    for name, value in data.items():
        print(f"  {name}: {value}")
    print(f"\nГистограмма сохранена как: {output_name}")
else:
    print("Не удалось извлечь данные из отчета!")