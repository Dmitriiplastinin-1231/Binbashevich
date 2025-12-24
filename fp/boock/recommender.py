"""
Модуль рекомендательной системы для книг.
Использует функциональное программирование для расчета рейтингов и фильтрации.
"""

from typing import Dict, List, Any, Callable
from functools import reduce
import json
import csv
from datetime import datetime


def calculate_match_score(
    book: Dict[str, Any],
    preferences: Dict[str, List[str]]
) -> float:
    """
    Вычисляет рейтинг соответствия книги предпочтениям пользователя.
    
    Args:
        book: Словарь с данными о книге
        preferences: Словарь с предпочтениями пользователя
        
    Returns:
        Числовой рейтинг соответствия
    """
    score = 0.0
    
    # Вес для разных критериев
    GENRE_WEIGHT = 3.0
    AUTHOR_WEIGHT = 2.5
    KEYWORD_WEIGHT = 1.0
    
    # Проверка жанра
    book_genre = book.get('genre_normalized', '')
    if any(genre in book_genre for genre in preferences.get('genres', [])):
        score += GENRE_WEIGHT
    
    # Проверка автора
    book_author = book.get('author_normalized', '')
    if any(author in book_author for author in preferences.get('authors', [])):
        score += AUTHOR_WEIGHT
    
    # Проверка ключевых слов
    book_keywords = book.get('keywords_normalized', [])
    user_keywords = preferences.get('keywords', [])
    
    matching_keywords = sum(
        1 for user_kw in user_keywords
        if any(user_kw in book_kw for book_kw in book_keywords)
    )
    score += matching_keywords * KEYWORD_WEIGHT
    
    return score


def add_score_to_book(
    book: Dict[str, Any],
    preferences: Dict[str, List[str]]
) -> Dict[str, Any]:
    """
    Добавляет рейтинг соответствия к данным книги.
    
    Args:
        book: Словарь с данными о книге
        preferences: Словарь с предпочтениями
        
    Returns:
        Словарь книги с добавленным рейтингом
    """
    book_with_score = book.copy()
    book_with_score['match_score'] = calculate_match_score(book, preferences)
    return book_with_score


def filter_by_genres(
    books: List[Dict[str, Any]],
    genres: List[str]
) -> List[Dict[str, Any]]:
    """
    Фильтрует книги по жанрам.
    
    Args:
        books: Список книг
        genres: Список жанров для фильтрации
        
    Returns:
        Отфильтрованный список книг
    """
    if not genres:
        return books
    
    normalized_genres = [g.lower().strip() for g in genres]
    
    return list(filter(
        lambda book: any(
            genre in book.get('genre_normalized', '')
            for genre in normalized_genres
        ),
        books
    ))


def filter_by_year(
    books: List[Dict[str, Any]],
    min_year: int = 0
) -> List[Dict[str, Any]]:
    """
    Фильтрует книги по минимальному году публикации.
    
    Args:
        books: Список книг
        min_year: Минимальный год публикации
        
    Returns:
        Отфильтрованный список книг
    """
    if min_year <= 0:
        return books
    
    return list(filter(
        lambda book: book.get('year', 0) >= min_year,
        books
    ))


def sort_by_score(books: List[Dict[str, Any]], reverse: bool = True) -> List[Dict[str, Any]]:
    """Сортирует книги по рейтингу соответствия."""
    return sorted(books, key=lambda book: book.get('match_score', 0), reverse=reverse)


def sort_by_title(books: List[Dict[str, Any]], reverse: bool = False) -> List[Dict[str, Any]]:
    """Сортирует книги по названию (алфавиту)."""
    return sorted(books, key=lambda book: book.get('title', ''), reverse=reverse)


def sort_by_year(books: List[Dict[str, Any]], reverse: bool = True) -> List[Dict[str, Any]]:
    """Сортирует книги по году публикации."""
    return sorted(books, key=lambda book: book.get('year', 0), reverse=reverse)


# Словарь с функциями сортировки
SORT_FUNCTIONS: Dict[str, Callable] = {
    'score': sort_by_score,
    'title': sort_by_title,
    'year': sort_by_year
}


def get_recommendations(
    books: List[Dict[str, Any]],
    preferences: Dict[str, List[str]],
    genre_filter: List[str] = None,
    min_year: int = 0,
    sort_by: str = 'score',
    limit: int = None
) -> List[Dict[str, Any]]:
    """
    Получает список рекомендованных книг на основе предпочтений.
    
    Args:
        books: Список книг из базы
        preferences: Словарь с предпочтениями пользователя
        genre_filter: Список жанров для фильтрации (опционально)
        min_year: Минимальный год публикации (опционально)
        sort_by: Критерий сортировки ('score', 'title', 'year')
        limit: Максимальное количество результатов (опционально)
        
    Returns:
        Список рекомендованных книг
    """
    # Композиция функций для обработки данных
    pipeline = [
        lambda b: list(map(lambda book: add_score_to_book(book, preferences), b)),
        lambda b: filter_by_genres(b, genre_filter) if genre_filter else b,
        lambda b: filter_by_year(b, min_year),
        lambda b: SORT_FUNCTIONS.get(sort_by, sort_by_score)(b),
        lambda b: b[:limit] if limit else b
    ]
    
    # Применяем pipeline к данным
    result = reduce(lambda data, func: func(data), pipeline, books)
    
    return result


def filter_recommendations(
    recommendations: List[Dict[str, Any]],
    min_score: float = 0.0
) -> List[Dict[str, Any]]:
    """
    Фильтрует рекомендации по минимальному рейтингу.
    
    Args:
        recommendations: Список рекомендаций
        min_score: Минимальный рейтинг
        
    Returns:
        Отфильтрованный список
    """
    return list(filter(
        lambda book: book.get('match_score', 0) >= min_score,
        recommendations
    ))


def save_recommendations_to_json(
    recommendations: List[Dict[str, Any]],
    filepath: str
) -> bool:
    """
    Сохраняет рекомендации в JSON файл.
    
    Args:
        recommendations: Список рекомендаций
        filepath: Путь к файлу для сохранения
        
    Returns:
        True при успешном сохранении, иначе False
    """
    try:
        # Подготавливаем данные для сохранения
        data_to_save = {
            'timestamp': datetime.now().isoformat(),
            'count': len(recommendations),
            'recommendations': [
                {
                    'title': book.get('title', ''),
                    'author': book.get('author', ''),
                    'genre': book.get('genre', ''),
                    'year': book.get('year', 0),
                    'description': book.get('description', ''),
                    'match_score': book.get('match_score', 0)
                }
                for book in recommendations
            ]
        }
        
        with open(filepath, 'w', encoding='utf-8') as file:
            json.dump(data_to_save, file, ensure_ascii=False, indent=2)
        
        return True
    except Exception as e:
        print(f"Ошибка при сохранении в JSON: {e}")
        return False


def save_recommendations_to_csv(
    recommendations: List[Dict[str, Any]],
    filepath: str
) -> bool:
    """
    Сохраняет рекомендации в CSV файл.
    
    Args:
        recommendations: Список рекомендаций
        filepath: Путь к файлу для сохранения
        
    Returns:
        True при успешном сохранении, иначе False
    """
    try:
        if not recommendations:
            return False
        
        fieldnames = ['title', 'author', 'genre', 'year', 'description', 'match_score']
        
        with open(filepath, 'w', encoding='utf-8', newline='') as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            
            for book in recommendations:
                writer.writerow({
                    'title': book.get('title', ''),
                    'author': book.get('author', ''),
                    'genre': book.get('genre', ''),
                    'year': book.get('year', 0),
                    'description': book.get('description', ''),
                    'match_score': book.get('match_score', 0)
                })
        
        return True
    except Exception as e:
        print(f"Ошибка при сохранении в CSV: {e}")
        return False


def create_reading_list(selected_books: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Создает список для чтения из выбранных книг.
    
    Args:
        selected_books: Список выбранных книг
        
    Returns:
        Список книг с добавленной информацией о статусе
    """
    return [
        {
            **book,
            'status': 'to_read',
            'added_at': datetime.now().isoformat()
        }
        for book in selected_books
    ]
