"""
Веб-приложение для рекомендательной системы книг.
Flask-приложение с русским интерфейсом.
"""

from flask import Flask, render_template, request, jsonify, send_file
import os
import json
from datetime import datetime

from data_loader import (
    load_books_from_json,
    filter_valid_books,
    normalize_book_data,
    get_all_genres,
    get_all_authors,
    get_year_range
)
from preferences import (
    create_preferences_from_strings,
    validate_preferences,
    get_preference_summary
)
from recommender import (
    get_recommendations,
    filter_recommendations,
    save_recommendations_to_json,
    save_recommendations_to_csv,
    create_reading_list
)

app = Flask(__name__)

# Путь к базе данных книг
BOOKS_DB_PATH = os.path.join(os.path.dirname(__file__), 'books_database.json')
EXPORT_DIR = os.path.join(os.path.dirname(__file__), 'exports')

# Создаем директорию для экспорта, если её нет
os.makedirs(EXPORT_DIR, exist_ok=True)

# Глобальная переменная для хранения загруженных книг
books_cache = []


def load_books():
    """Загружает и кэширует книги из базы данных."""
    global books_cache
    if not books_cache:
        raw_books = load_books_from_json(BOOKS_DB_PATH)
        valid_books = filter_valid_books(raw_books)
        books_cache = [normalize_book_data(book) for book in valid_books]
    return books_cache


@app.route('/')
def index():
    """Главная страница приложения."""
    books = load_books()
    genres = get_all_genres(books)
    authors = get_all_authors(books)
    year_min, year_max = get_year_range(books)
    
    return render_template(
        'index.html',
        genres=genres,
        authors=authors,
        year_min=year_min,
        year_max=year_max,
        total_books=len(books)
    )


@app.route('/api/recommend', methods=['POST'])
def recommend():
    """API endpoint для получения рекомендаций."""
    try:
        data = request.get_json()
        
        # Получаем данные из запроса
        genres_str = data.get('genres', '')
        authors_str = data.get('authors', '')
        keywords_str = data.get('keywords', '')
        genre_filter = data.get('genre_filter', [])
        min_year = int(data.get('min_year', 0))
        sort_by = data.get('sort_by', 'score')
        limit = data.get('limit')
        
        if limit:
            limit = int(limit)
        
        # Создаем предпочтения
        preferences = create_preferences_from_strings(
            genres_str, authors_str, keywords_str
        )
        
        # Получаем книги
        books = load_books()
        
        # Получаем рекомендации
        recommendations = get_recommendations(
            books,
            preferences,
            genre_filter=genre_filter if genre_filter else None,
            min_year=min_year,
            sort_by=sort_by,
            limit=limit
        )
        
        # Фильтруем по минимальному score только если есть предпочтения
        if validate_preferences(preferences):
            recommendations = filter_recommendations(recommendations, min_score=0.1)
        
        # Все рекомендации должны содержать match_score (хотя бы 0)
        
        # Подготавливаем данные для отправки
        result = {
            'success': True,
            'count': len(recommendations),
            'preferences_summary': get_preference_summary(preferences),
            'recommendations': [
                {
                    'title': book['title'],
                    'author': book['author'],
                    'genre': book['genre'],
                    'year': book['year'],
                    'description': book['description'],
                    'match_score': round(book['match_score'], 2),
                    'keywords': book.get('keywords', [])
                }
                for book in recommendations
            ]
        }
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Ошибка при обработке запроса: {str(e)}'
        }), 500


@app.route('/api/export', methods=['POST'])
def export_recommendations():
    """API endpoint для экспорта рекомендаций."""
    try:
        data = request.get_json()
        recommendations = data.get('recommendations', [])
        format_type = data.get('format', 'json')
        
        if not recommendations:
            return jsonify({
                'success': False,
                'error': 'Нет данных для экспорта'
            }), 400
        
        # Генерируем имя файла
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        if format_type == 'json':
            filename = f'recommendations_{timestamp}.json'
            filepath = os.path.join(EXPORT_DIR, filename)
            
            export_data = {
                'timestamp': datetime.now().isoformat(),
                'count': len(recommendations),
                'recommendations': recommendations
            }
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)
                
        elif format_type == 'csv':
            filename = f'recommendations_{timestamp}.csv'
            filepath = os.path.join(EXPORT_DIR, filename)
            
            import csv
            fieldnames = ['title', 'author', 'genre', 'year', 'description', 'match_score']
            
            with open(filepath, 'w', encoding='utf-8', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                for rec in recommendations:
                    writer.writerow({
                        'title': rec.get('title', ''),
                        'author': rec.get('author', ''),
                        'genre': rec.get('genre', ''),
                        'year': rec.get('year', 0),
                        'description': rec.get('description', ''),
                        'match_score': rec.get('match_score', 0)
                    })
        else:
            return jsonify({
                'success': False,
                'error': 'Неподдерживаемый формат'
            }), 400
        
        return jsonify({
            'success': True,
            'filename': filename,
            'filepath': filepath
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Ошибка при экспорте: {str(e)}'
        }), 500


@app.route('/api/download/<filename>')
def download_file(filename):
    """API endpoint для скачивания файла."""
    try:
        filepath = os.path.join(EXPORT_DIR, filename)
        if os.path.exists(filepath):
            return send_file(filepath, as_attachment=True)
        else:
            return jsonify({
                'success': False,
                'error': 'Файл не найден'
            }), 404
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Ошибка при скачивании: {str(e)}'
        }), 500


@app.route('/api/stats')
def get_stats():
    """API endpoint для получения статистики по базе книг."""
    books = load_books()
    genres = get_all_genres(books)
    authors = get_all_authors(books)
    year_min, year_max = get_year_range(books)
    
    return jsonify({
        'total_books': len(books),
        'total_genres': len(genres),
        'total_authors': len(authors),
        'year_range': [year_min, year_max],
        'genres': genres,
        'authors': authors
    })


if __name__ == '__main__':
    print("=" * 60)
    print("Рекомендательная система для выбора книг")
    print("=" * 60)
    print(f"База данных: {BOOKS_DB_PATH}")
    print(f"Директория экспорта: {EXPORT_DIR}")
    
    # Загружаем книги при запуске
    books = load_books()
    print(f"Загружено книг: {len(books)}")
    
    print("\nСервер запускается...")
    print("Откройте в браузере: http://localhost:5000")
    print("=" * 60)
    
    app.run(debug=True, host='0.0.0.0', port=5000)
