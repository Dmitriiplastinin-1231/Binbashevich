import os
import re
import numpy as np
from pathlib import Path
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
import pymorphy3
import nltk
from nltk.corpus import stopwords
import matplotlib.pyplot as plt
from wordcloud import WordCloud
import argparse

nltk.download('stopwords')

morph = pymorphy3.MorphAnalyzer()
base_stopwords = set(stopwords.words('russian'))
custom_stopwords = {
    'это', 'который', 'mash', 'риа', 'фонтанка', 'рбк', 'также', 'подписаться', 'год', 'подписываться',
    'весь', '2025', 'всё', 'её', 'пока', 'тыс', 'млн', 'www', 'м', '000',
    'свой', 'новость', 'fontankaspb', 'club', 'cpwupt', 'from',
    'https', 'habr', 'ru', 'com', 'rt', 'u', 'vk', 'club194944166', 'эфир', 'прямой', 'ecotopor'
}
custom_stopwords = custom_stopwords.union([str(i) for i in range(1000)] + [f"20{i}" for i in range(10, 30)])
custom_stopwords = {morph.parse(w)[0].normal_form for w in custom_stopwords}
all_stopwords = base_stopwords.union(custom_stopwords)

def process_file(filepath):
    local_morph = pymorphy3.MorphAnalyzer()
    with open(filepath, encoding='utf-8-sig') as file:
        text = file.read()

    words = re.findall(r'\w+', text.lower())
    filtered_words = [w for w in words if w not in all_stopwords]
    lemmas = [local_morph.parse(w)[0].normal_form for w in filtered_words]
    filtered_lemmas = [l for l in lemmas if l not in all_stopwords]
    return Counter(filtered_lemmas)

def main():

    parser = argparse.ArgumentParser(description="Merge paser for sources from telegram, vkontakte and detached ones.")
    parser.add_argument("--input", type=str, default="data", help="Input directory with parsed CSV files.")
    parser.add_argument("--output", type=str, default="sources_analytics", help="Output directory for visualization.")
    args = parser.parse_args()

    os.makedirs(args.output, exist_ok=True)

    folder = args.input
    files = [os.path.join(folder, f) for f in os.listdir(folder) if f.endswith(".csv")]
    group_names = [os.path.splitext(os.path.basename(f))[0] for f in files]

    print(f"Найдено {len(files)} файлов для обработки: {group_names}")

    with ProcessPoolExecutor() as executor:
        counters = list(executor.map(process_file, files))

    filtered_entries = [
        (name, counter) for name, counter in zip(group_names, counters)
    ]
    filtered_names = [name for name, _ in filtered_entries]
    filtered_counters = [counter for _, counter in filtered_entries]

    total_counter = Counter()
    for c in counters:
        total_counter.update(c)

    top_n = 20
    top_words = [w for w, _ in total_counter.most_common(top_n)]
    words, freqs = zip(*total_counter.most_common(top_n))
    cnt = 1

    # === Гистограмма (Stacked Bar) ===
    freq_matrix = np.array([[counter[word] for counter in filtered_counters] for word in top_words])
    x = np.arange(len(top_words))
    plt.figure(figsize=(12, 8))
    bottom = np.zeros(len(top_words))
    for i, group in enumerate(filtered_names):
        plt.bar(x, freq_matrix[:, i], bottom=bottom, label=group)
        bottom += freq_matrix[:, i]

    plt.xticks(x, top_words, rotation=45, ha='right')
    plt.ylabel('Частота')
    plt.title(f'Топ-{top_n} слов по каналам (Stacked Bar)')
    plt.legend(title='Канал')
    plt.tight_layout()
    plt.savefig(f'{args.output}/analytics{cnt}')
    cnt += 1    

    # === Горизонтальная гистограмма ===
    plt.figure(figsize=(12, 8))
    plt.barh(words, freqs)
    plt.gca().invert_yaxis()
    plt.xlabel('Частота')
    plt.title(f'Top-{top_n} наиболее употребимых слов')
    plt.tight_layout()
    plt.savefig(f'{args.output}/analytics{cnt}')
    cnt += 1

    # === WordCloud ===
    wordcloud = WordCloud(width=1000, height=600, background_color='white', colormap='plasma')
    wordcloud.generate_from_frequencies(total_counter)
    plt.figure(figsize=(12, 8))
    plt.imshow(wordcloud, interpolation='bilinear')
    plt.axis('off')
    plt.title('Облако наиболее частых слов')
    plt.tight_layout()
    plt.savefig(f'{args.output}/analytics{cnt}')
    cnt += 1

    # === Круговая диаграмма ===
    plt.figure(figsize=(12, 8))
    plt.pie(
        freqs,
        labels=words,
        autopct='%1.1f%%',
        startangle=140,
        wedgeprops={'edgecolor': 'white'}
    )
    plt.title(f'Доля топ-{top_n} слов в общем количестве')
    plt.tight_layout()
    plt.savefig(f'{args.output}/analytics{cnt}')
    cnt += 1

    output_txt_path = os.path.join(args.output, "word_frequencies.txt")
    with open(output_txt_path, "w", encoding="utf-8") as f:
        for word, count in total_counter.most_common():
            f.write(f"{word}: {count}\n")
    print(f"Файл с частотами сохранён: {output_txt_path}")

if __name__ == "__main__":
    main()
    print('Analytics done!')