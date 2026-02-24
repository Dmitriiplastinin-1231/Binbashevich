import os
import pandas as pd

folder = './data'
output_file = 'totals/detached_sources.csv'

# Все источники, не входящие в telegram/vkontakte
# (Telegram и VK сами пишут в totals/)
detached_csv_files = [
    'habr.csv', 'vc.csv', 'rbc.csv',
    'lentaru.csv', 'tass.csv', 'kommersant.csv',
    'gazeta.csv', 'izvestia.csv',
]

all_data = []

for file in detached_csv_files:
    file_path = os.path.join(folder, file)
    if not os.path.exists(file_path):
        print(f'Файл {file_path} не найден, пропускаю...')
        continue
    print(f'Обрабатываю {file_path}...')
    df = pd.read_csv(file_path, header=None)
    all_data.append(df)

os.makedirs("totals", exist_ok=True)
if all_data:
    combined_df = pd.concat(all_data, ignore_index=True)
    combined_df.to_csv(output_file, index=False, header=False, encoding='utf-8-sig')
    print(f'\nГотово! Объединено {len(all_data)} файлов в {output_file}')
else:
    print('Нет данных для объединения.')