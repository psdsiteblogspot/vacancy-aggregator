#!/usr/bin/env python3
"""
Скрипт для парсинга вакансий с HeadHunter с улучшенной отладкой
"""

import json
import requests
from datetime import datetime
import time
import sys
import os

# Конфигурация
CONFIG = {
    'base_url': 'https://api.hh.ru/vacancies',
    'search_params': {
        'text': 'Системный администратор',
        'area': '113',  # Россия
        'search_field': 'name',
        'order_by': 'publication_time',
        'period': '1',
        'per_page': '50',  # Уменьшено для тестирования
        'page': '0',
        'schedule': 'remote',
    },
    'headers': {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    },
    'output_file': 'hh_vacancies.json',
    'max_pages': 2  # Уменьшено для тестирования
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

def test_api_connection():
    """Тестирует соединение с API"""
    print("🔍 Тестирование соединения с API HeadHunter...")
    try:
        response = requests.get(
            'https://api.hh.ru/vacancies',
            params={'text': 'test', 'per_page': '1'},
            headers=CONFIG['headers'],
            timeout=10
        )
        print(f"✅ Статус ответа: {response.status_code}")
        if response.status_code == 200:
            print("✅ API доступен")
            return True
        else:
            print(f"❌ API вернул ошибку: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Ошибка соединения: {e}")
        return False

def fetch_vacancies(page=0):
    """Загружает вакансии с указанной страницы"""
    params = CONFIG['search_params'].copy()
    params['page'] = str(page)
    
    print(f"📡 Запрос к API, страница {page + 1}...")
    print(f"   URL: {CONFIG['base_url']}")
    print(f"   Параметры: {params}")
    
    try:
        response = requests.get(
            CONFIG['base_url'],
            params=params,
            headers=CONFIG['headers'],
            timeout=30
        )
        
        print(f"   Статус: {response.status_code}")
        
        if response.status_code != 200:
            print(f"   ❌ Ошибка: {response.text}")
            return None
            
        return response.json()
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Ошибка при запросе: {e}")
        return None

def parse_vacancy(item):
    """Парсит данные одной вакансии"""
    return {
        'title': item['name'],
        'company': item['employer']['name'],
        'salary': format_salary(item.get('salary')),
        'publishDate': item['published_at'].split('T')[0],
        'url': item['alternate_url'],
        'experience': item.get('experience', {}).get('name', 'Не указан'),
        'employment': item.get('employment', {}).get('name', 'Не указано'),
        'schedule': item.get('schedule', {}).get('name', 'Не указан'),
        'area': item.get('area', {}).get('name', 'Не указано'),
    }

def main():
    """Основная функция"""
    print("🚀 Запуск парсинга вакансий с HeadHunter")
    print(f"📅 Время запуска: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🔧 Рабочая директория: {os.getcwd()}")
    print(f"📁 Файлы в директории: {', '.join(os.listdir('.'))}")
    
    # Тестируем API
    if not test_api_connection():
        print("❌ Не удалось подключиться к API")
        sys.exit(1)
    
    all_vacancies = []
    
    # Загружаем первую страницу
    print("\n📋 Загрузка вакансий...")
    data = fetch_vacancies(0)
    
    if not data:
        print("❌ Не удалось загрузить данные")
        # Создаем файл с демо-данными
        print("📝 Создаем файл с демо-данными...")
        demo_data = {
            'source': 'hh.ru',
            'updated': datetime.now().isoformat() + 'Z',
            'total_found': 0,
            'vacancies_count': 0,
            'search_params': CONFIG['search_params'],
            'vacancies': [],
            'error': 'Failed to fetch data from API'
        }
        
        with open(CONFIG['output_file'], 'w', encoding='utf-8') as f:
            json.dump(demo_data, f, ensure_ascii=False, indent=2)
        
        print(f"✅ Создан файл {CONFIG['output_file']} с демо-данными")
        sys.exit(0)
    
    total_found = data.get('found', 0)
    pages = data.get('pages', 1)
    
    print(f"📊 Найдено вакансий: {total_found}")
    print(f"📄 Страниц: {pages}")
    
    # Парсим вакансии
    for item in data.get('items', []):
        all_vacancies.append(parse_vacancy(item))
    
    # Загружаем остальные страницы
    pages_to_load = min(pages, CONFIG['max_pages'])
    for page in range(1, pages_to_load):
        print(f"\n📄 Загрузка страницы {page + 1}/{pages_to_load}...")
        time.sleep(0.5)
        
        data = fetch_vacancies(page)
        if data:
            for item in data.get('items', []):
                all_vacancies.append(parse_vacancy(item))
    
    # Сортируем по дате
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
    print(f"\n💾 Сохранение в файл {CONFIG['output_file']}...")
    
    try:
        with open(CONFIG['output_file'], 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        # Проверяем, что файл создан
        if os.path.exists(CONFIG['output_file']):
            file_size = os.path.getsize(CONFIG['output_file'])
            print(f"✅ Файл создан успешно")
            print(f"📏 Размер файла: {file_size} байт")
            print(f"📊 Сохранено вакансий: {len(all_vacancies)}")
            
            # Показываем первые 3 вакансии
            if all_vacancies:
                print("\n📌 Последние вакансии:")
                for i, vac in enumerate(all_vacancies[:3], 1):
                    print(f"\n{i}. {vac['title']}")
                    print(f"   💼 {vac['company']}")
                    print(f"   💰 {vac['salary']}")
        else:
            print("❌ Файл не был создан!")
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ Ошибка при сохранении: {e}")
        sys.exit(1)
    
    print(f"\n✅ Парсинг завершен успешно!")
    print(f"🕒 Время завершения: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()
