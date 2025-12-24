import os
import pandas as pd

folder = './data'
output_file = 'totals/detached_sources.csv'

# Собираем список всех CSV в папке
csv_files = ['habr.csv', 'vc.csv', 'rbc.csv']

all_data = []

for file in csv_files:
    file_path = os.path.join(folder, file)
    print(f'Обрабатываю {file_path}...')
    df = pd.read_csv(file_path, header=None)
    all_data.append(df)

os.makedirs("totals", exist_ok=True)
combined_df = pd.concat(all_data, ignore_index=True)
combined_df.to_csv(output_file, index=False, header=False, encoding='utf-8-sig')

print(f'\n Готово! Объединено {len(csv_files)} файлов в {output_file}')