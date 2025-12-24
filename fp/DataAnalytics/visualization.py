from flask import Flask, render_template, send_from_directory, abort
from pathlib import Path
import os


app = Flask(__name__)

# Пути к папкам с аналитикой
SOURCES_DIR = Path("sources_analytics")
NETWORKS_DIR = Path("networks_analytics")

telegram_sources = ['Фонтанка SPB Online', 'РИА Новости', 'Топор. Экономика.', 'Mash', 'Прямой Эфир • Новости']
vk_sources = ["Комсомольская правда (kpru)", "NEWS.ru (nws_ru)", "Russia Today (rt_russian)",
               "Новости дня (ndnews24)", 'Вести (vesti)']

# Основные группы и подгруппы
GROUPS = {
    "telegram": telegram_sources,
    "vkontakte": vk_sources,
    "detached_sources": [source for source in os.listdir(Path("data"))
                         if source not in telegram_sources and source not in vk_sources]
}

@app.route("/")
def index():
    # Список изображений в папке
    def list_images(folder: Path):
        if not folder.exists():
            return []
        return sorted([p.name for p in folder.glob("analytics*.png")])

    sources_images = list_images(SOURCES_DIR)
    networks_images = list_images(NETWORKS_DIR)

    # Чтение частот слов
    freq_file = SOURCES_DIR / "word_frequencies.txt"
    word_freqs = []
    if freq_file.exists():
        with freq_file.open("r", encoding="utf-8") as f:
            counter = 0
            for line in f:
                line = line.strip()
                if not line:
                    continue
                if ":" in line:
                    word, count = line.split(":", 1)
                    word_freqs.append({"word": word.strip(), "count": int(count.strip())})
                else:
                    parts = line.split()
                    if len(parts) >= 2 and parts[-1].isdigit():
                        count = int(parts[-1])
                        word = " ".join(parts[:-1])
                        word_freqs.append({"word": word, "count": count})
                counter += 1
                if counter >= 100: break

    return render_template(
        "index.html",
        sources_images=sources_images,
        networks_images=networks_images,
        word_freqs=word_freqs,
        groups=GROUPS
    )

@app.route('/sources/<path:filename>')
def serve_sources(filename):
    if not (SOURCES_DIR.exists() and (SOURCES_DIR / filename).exists()):
        abort(404)
    return send_from_directory(str(SOURCES_DIR), filename)

@app.route('/networks/<path:filename>')
def serve_networks(filename):
    if not (NETWORKS_DIR.exists() and (NETWORKS_DIR / filename).exists()):
        abort(404)
    return send_from_directory(str(NETWORKS_DIR), filename)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
