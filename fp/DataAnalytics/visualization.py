from flask import Flask, render_template, send_from_directory, abort
from pathlib import Path
import os


app = Flask(__name__)

# Пути к папкам с аналитикой
SOURCES_DIR = Path("sources_analytics")
NETWORKS_DIR = Path("networks_analytics")

# 10 источников данных:
# 1. Telegram (группы)  2. VKontakte (группы)
# 3. RBC  4. VC.ru  5. Habr  6. Lenta.ru  7. ТАСС  8. Коммерсантъ  9. Газета.ру  10. Известия

GROUPS = {
    "telegram": "Telegram (группы пользователя)",
    "vkontakte": "VKontakte (группы пользователя)",
    "detached_sources": [
        "RBC (rbc.csv)",
        "VC.ru (vc.csv)",
        "Habr (habr.csv)",
        "Lenta.ru (lentaru.csv)",
        "ТАСС (tass.csv)",
        "Коммерсантъ (kommersant.csv)",
        "Газета.ру (gazeta.csv)",
        "Известия (izvestia.csv)",
    ]
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
