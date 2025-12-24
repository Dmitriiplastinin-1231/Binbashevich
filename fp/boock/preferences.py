"""
Модуль обработки пользовательских предпочтений.
Использует функциональное программирование для обработки данных.
"""

from typing import Dict, List, Any
from functools import reduce


def parse_preferences(
    genres: List[str],
    authors: List[str],
    keywords: List[str]
) -> Dict[str, List[str]]:
    """
    Парсит и нормализует пользовательские предпочтения.
    
    Args:
        genres: Список любимых жанров
        authors: Список любимых авторов
        keywords: Список ключевых слов
        
    Returns:
        Словарь с нормализованными предпочтениями
    """
    normalize = lambda s: s.lower().strip() if s else ""
    
    return {
        'genres': list(filter(None, map(normalize, genres))),
        'authors': list(filter(None, map(normalize, authors))),
        'keywords': list(filter(None, map(normalize, keywords)))
    }


def validate_preferences(preferences: Dict[str, List[str]]) -> bool:
    """
    Проверяет валидность пользовательских предпочтений.
    
    Args:
        preferences: Словарь с предпочтениями
        
    Returns:
        True, если предпочтения валидны, иначе False
    """
    required_keys = ['genres', 'authors', 'keywords']
    
    # Проверяем наличие всех необходимых ключей
    if not all(key in preferences for key in required_keys):
        return False
    
    # Проверяем, что хотя бы одно поле заполнено
    has_data = any(
        preferences[key] and len(preferences[key]) > 0 
        for key in required_keys
    )
    
    return has_data


def split_input_string(input_str: str, delimiter: str = ',') -> List[str]:
    """
    Разделяет строку на список элементов.
    
    Args:
        input_str: Входная строка
        delimiter: Разделитель (по умолчанию запятая)
        
    Returns:
        Список элементов
    """
    if not input_str:
        return []
    
    return [item.strip() for item in input_str.split(delimiter) if item.strip()]


def create_preferences_from_strings(
    genres_str: str = "",
    authors_str: str = "",
    keywords_str: str = ""
) -> Dict[str, List[str]]:
    """
    Создает словарь предпочтений из строк.
    
    Args:
        genres_str: Строка с жанрами через запятую
        authors_str: Строка с авторами через запятую
        keywords_str: Строка с ключевыми словами через запятую
        
    Returns:
        Словарь с предпочтениями
    """
    genres = split_input_string(genres_str)
    authors = split_input_string(authors_str)
    keywords = split_input_string(keywords_str)
    
    return parse_preferences(genres, authors, keywords)


def get_preference_summary(preferences: Dict[str, List[str]]) -> str:
    """
    Создает текстовое описание предпочтений пользователя.
    
    Args:
        preferences: Словарь с предпочтениями
        
    Returns:
        Текстовое описание
    """
    summary_parts = []
    
    if preferences.get('genres'):
        genres_str = ", ".join(preferences['genres'])
        summary_parts.append(f"Жанры: {genres_str}")
    
    if preferences.get('authors'):
        authors_str = ", ".join(preferences['authors'])
        summary_parts.append(f"Авторы: {authors_str}")
    
    if preferences.get('keywords'):
        keywords_str = ", ".join(preferences['keywords'])
        summary_parts.append(f"Ключевые слова: {keywords_str}")
    
    if not summary_parts:
        return "Показаны все книги из базы данных"
    
    return "; ".join(summary_parts)
