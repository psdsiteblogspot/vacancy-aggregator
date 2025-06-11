#!/usr/bin/env python3
"""
Скрипт для парсинга вакансий системного администратора с HeadHunter
Работает через публичный API без необходимости в ключе
"""

import json
import requests
from datetime import datetime
import time
import sys

# Конфигурация
CONFIG = {
    'base_url': 'https://api.hh.ru/vacancies',
    'search_params': {
        'text': 'Системный администратор',
        'area': '113',  # Россия (1 - Москва, 2 - СПб)
        'search_field': 'name',
        'order_by': 'publication_time',
        'period': '1',  # За последний день
        'per_page': '100',
        'page': '0',
        'schedule': 'remote',  # Удаленная работа
        # 'only_with_salary': 'true',  # Только с зарплатой
        # 'salary': '100000',  # Минимальная зарплата
    },
    'headers': {
        'User-Agent': 'GitHub Actions Vacancy Parser/1.0'
    },
    'output_file': 'hh_vacancies.json',
    'max_pages': 5  # Максимум страниц для парсинга
}

def format_salary(salary):
    """Форматирует информацию о зарплате"""
    if not salary:
        return 'Зарплата не указана'
    
    parts = []
    if salary.get('from'):
        parts.append(f"от {salary['from']:,}".replace(',', ' '))
    if salary.get('to'):
        parts.append(f"до {salary['to']:,}".replace(',', ' '))
    
    if parts:
        result = ' '.join(parts)
        currency = salary.get('currency', 'RUR')
        if currency == 'RUR':
            result += ' руб.'
        else:
            result += f' {currency}'
        return result
    
    return 'Зарплата не указана'

def fetch_vacancies(page=0):
    """Загружает вакансии с указанной страницы"""
    params = CONFIG['search_params'].copy()
    params['page'] = str(page)
    
    try:
        response = requests.get(
            CONFIG['base_url'],
            params=params,
            headers=CONFIG['headers'],
            timeout=30
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"❌ Ошибка при запросе к API: {e}")
        return None

def parse_vacancy(item):
    """Парсит данные одной вакансии"""
    return {
        'title': item['name'],
        'company': item['employer']['name'],
        'salary': format_salary(item.get('salary')),
        'publishDate': item['published_at'].split('T')[0],
        'url': item['alternate_url'],
        # Дополнительные поля
        'experience': item.get('experience', {}).get('name', 'Не указан'),
        'employment': item.get('employment', {}).get('name', 'Не указано'),
        'schedule': item.get('schedule', {}).get('name', 'Не указан'),
        'area': item.get('area', {}).get('name', 'Не указано'),
        'description': item.get('snippet', {}).get('requirement', ''),
        'responsibility': item.get('snippet', {}).get('responsibility', ''),
    }

def main():
    """Основная функция"""
    print("🚀 Запуск парсинга вакансий с HeadHunter...")
    print(f"📋 Параметры поиска: {CONFIG['search_params']['text']}")
    
    all_vacancies = []
    
    # Загружаем первую страницу
    data = fetch_vacancies(0)
    if not data:
        print("❌ Не удалось загрузить данные")
        sys.exit(1)
    
    total_found = data.get('found', 0)
    pages = data.get('pages', 1)
    
    print(f"📊 Найдено вакансий: {total_found}")
    print(f"📄 Страниц: {pages}")
    
    # Парсим вакансии с первой страницы
    for item in data.get('items', []):
        all_vacancies.append(parse_vacancy(item))
    
    # Загружаем остальные страницы (если есть)
    pages_to_load = min(pages, CONFIG['max_pages'])
    for page in range(1, pages_to_load):
        print(f"📄 Загрузка страницы {page + 1}/{pages_to_load}...")
        time.sleep(0.5)  # Задержка между запросами
        
        data = fetch_vacancies(page)
        if data:
            for item in data.get('items', []):
                all_vacancies.append(parse_vacancy(item))
    
    # Сортируем по дате публикации (новые первыми)
    all_vacancies.sort(key=lambda x: x['publishDate'], reverse=True)
    
    # Формируем результат
    result = {
        'source': 'hh.ru',
        'updated': datetime.now().isoformat() + 'Z',
        'total_found': total_found,
        'vacancies_count': len(all_vacancies),
        'search_params': CONFIG['search_params'],
        'vacancies': all_vacancies
    }
    
    # Сохраняем в файл
    try:
        with open(CONFIG['output_file'], 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        print(f"✅ Успешно сохранено {len(all_vacancies)} вакансий в {CONFIG['output_file']}")
        print(f"🕒 Время обновления: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Показываем последние вакансии
        print("\n📌 Последние 5 вакансий:")
        for i, vacancy in enumerate(all_vacancies[:5], 1):
            print(f"\n{i}. {vacancy['title']}")
            print(f"   💼 {vacancy['company']}")
            print(f"   💰 {vacancy['salary']}")
            print(f"   📅 {vacancy['publishDate']}")
            print(f"   📍 {vacancy['area']}")
        
    except Exception as e:
        print(f"❌ Ошибка при сохранении файла: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
