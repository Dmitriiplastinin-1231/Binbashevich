"""
Модуль для загрузки данных книг из файла JSON.
Использует функциональный подход для обработки данных.
"""

import json
from typing import List, Dict, Any
from functools import reduce


def load_books_from_json(filepath: str) -> List[Dict[str, Any]]:
    """
    Загружает книги из JSON файла.
    
    Args:
        filepath: Путь к JSON файлу с базой книг
        
    Returns:
        Список словарей с данными о книгах
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as file:
            books = json.load(file)
        return books
    except FileNotFoundError:
        print(f"Ошибка: Файл {filepath} не найден.")
        return []
    except json.JSONDecodeError:
        print(f"Ошибка: Невозможно прочитать JSON из {filepath}.")
        return []


def validate_book(book: Dict[str, Any]) -> bool:
    """
    Проверяет корректность данных книги.
    
    Args:
        book: Словарь с данными о книге
        
    Returns:
        True, если книга валидна, иначе False
    """
    required_fields = ['title', 'author', 'genre', 'description', 'year']
    return all(field in book for field in required_fields)


def filter_valid_books(books: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Фильтрует список книг, оставляя только валидные записи.
    
    Args:
        books: Список книг
        
    Returns:
        Список валидных книг
    """
    return list(filter(validate_book, books))


def normalize_string(s: str) -> str:
    """
    Нормализует строку: приводит к нижнему регистру и удаляет лишние пробелы.
    
    Args:
        s: Исходная строка
        
    Returns:
        Нормализованная строка
    """
    return s.lower().strip()


def normalize_book_data(book: Dict[str, Any]) -> Dict[str, Any]:
    """
    Нормализует данные книги для упрощения поиска и сравнения.
    
    Args:
        book: Словарь с данными о книге
        
    Returns:
        Словарь с нормализованными данными
    """
    normalized = book.copy()
    
    # Нормализуем текстовые поля
    if 'genre' in normalized:
        normalized['genre_normalized'] = normalize_string(normalized['genre'])
    if 'author' in normalized:
        normalized['author_normalized'] = normalize_string(normalized['author'])
    if 'keywords' in normalized and isinstance(normalized['keywords'], list):
        normalized['keywords_normalized'] = [normalize_string(kw) for kw in normalized['keywords']]
    else:
        normalized['keywords_normalized'] = []
        
    return normalized


def get_all_genres(books: List[Dict[str, Any]]) -> List[str]:
    """
    Извлекает список всех уникальных жанров из базы книг.
    
    Args:
        books: Список книг
        
    Returns:
        Список уникальных жанров
    """
    genres = map(lambda book: book.get('genre', ''), books)
    unique_genres = list(set(genres))
    return sorted([g for g in unique_genres if g])


def get_all_authors(books: List[Dict[str, Any]]) -> List[str]:
    """
    Извлекает список всех уникальных авторов из базы книг.
    
    Args:
        books: Список книг
        
    Returns:
        Список уникальных авторов
    """
    authors = map(lambda book: book.get('author', ''), books)
    unique_authors = list(set(authors))
    return sorted([a for a in unique_authors if a])


def get_year_range(books: List[Dict[str, Any]]) -> tuple:
    """
    Определяет диапазон годов публикации книг в базе.
    
    Args:
        books: Список книг
        
    Returns:
        Кортеж (минимальный_год, максимальный_год)
    """
    if not books:
        return (0, 0)
    
    years = [book.get('year', 0) for book in books if book.get('year')]
    
    if not years:
        return (0, 0)
    
    return (min(years), max(years))
