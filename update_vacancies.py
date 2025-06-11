#!/usr/bin/env python3    
import json
import requests
import time
from datetime import datetime

def get_vacancies():
    """Получение вакансий с API HeadHunter"""
    
    url = "https://api.hh.ru/vacancies"
    headers = {
        'User-Agent': 'VacancyAggregator/1.0 (gradelift.ru)'
    }
    
    params = {
        'text': 'Системный администратор',
        'area': '113',  # Россия
        'search_field': 'name',
        'per_page': 50,
        'page': 0,
        'order_by': 'salary_desc',
        'search_period': 1,  # За последний день (как на hh.ru)
        'only_with_salary': 'true',
        'schedule': 'remote',
        'currency': 'RUR'
    }
    
    try:
        print("🔍 Запрос к API HeadHunter...")
        response = requests.get(url, params=params, headers=headers, timeout=10)
        
        print(f"📡 Статус: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            items = data.get('items', [])
            found = data.get('found', 0)
            
            print(f"✅ Найдено: {found} вакансий")
            print(f"📄 Получено: {len(items)} вакансий")
            
            return items
        else:
            print(f"❌ Ошибка API: {response.status_code}")
            return []
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return []

def format_vacancy(item):
    """Форматирование одной вакансии"""
    try:
        # Базовые данные
        vacancy_id = str(item.get('id', ''))
        title = item.get('name', 'Без названия')
        url = item.get('alternate_url', '')
        
        # Работодатель
        employer = item.get('employer') or {}
        company = employer.get('name', 'Не указана')
        
        # Зарплата
        salary_data = item.get('salary')
        if salary_data:
            salary_from = salary_data.get('from')
            salary_to = salary_data.get('to')
            currency = salary_data.get('currency', 'RUR')
            
            if salary_from and salary_to:
                salary = f"от {salary_from:,} до {salary_to:,} руб.".replace(',', ' ')
            elif salary_from:
                salary = f"от {salary_from:,} руб.".replace(',', ' ')
            else:
                salary = "Зарплата не указана"
        else:
            salary = "Зарплата не указана"
        
        # Дата публикации
        published = item.get('published_at', '')
        if published:
            try:
                dt = datetime.fromisoformat(published.replace('Z', '+00:00'))
                publish_date = dt.strftime('%Y-%m-%d')
            except:
                publish_date = published[:10] if len(published) >= 10 else ''
        else:
            publish_date = ''
        
        # Дополнительные данные
        area_data = item.get('area') or {}
        area = area_data.get('name', '')
        
        experience_data = item.get('experience') or {}
        experience = experience_data.get('name', '')
        
        employment_data = item.get('employment') or {}
        employment = employment_data.get('name', '')
        
        schedule_data = item.get('schedule') or {}
        schedule = schedule_data.get('name', '')
        
        return {
            'id': vacancy_id,
            'title': title,
            'company': company,
            'salary': salary,
            'publishDate': publish_date,
            'url': url,
            'area': area,
            'experience': experience,
            'employment': employment,
            'schedule': schedule
        }
        
    except Exception as e:
        print(f"⚠️ Ошибка обработки вакансии: {e}")
        return None

def main():
    print("🚀 Запуск парсера вакансий HH.ru")
    print("=" * 50)
    
    # Получаем вакансии
    raw_vacancies = get_vacancies()
    
    if not raw_vacancies:
        print("❌ Не удалось получить вакансии")
        # Создаем пустой файл
        empty_data = {
            'source': 'hh.ru',
            'updated': datetime.now().isoformat() + 'Z',
            'vacancies': []
        }
        with open('hh_vacancies.json', 'w', encoding='utf-8') as f:
            json.dump(empty_data, f, ensure_ascii=False, indent=2)
        return
    
    # Обрабатываем вакансии
    formatted_vacancies = []
    for item in raw_vacancies:
        formatted = format_vacancy(item)
        if formatted:
            formatted_vacancies.append(formatted)
    
    print(f"✅ Обработано: {len(formatted_vacancies)} вакансий")
    
    # Создаем итоговый JSON
    result = {
        'source': 'hh.ru',
        'updated': datetime.now().isoformat() + 'Z',
        'search_parameters': {
            'text': 'Системный администратор',
            'area': '113',
            'schedule': 'remote',
            'only_with_salary': True
        },
        'statistics': {
            'total_loaded': len(formatted_vacancies)
        },
        'vacancies': formatted_vacancies
    }
    
    # Сохраняем файл
    try:
        with open('hh_vacancies.json', 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        print(f"✅ Файл hh_vacancies.json создан!")
        print(f"📁 Сохранено: {len(formatted_vacancies)} вакансий")
        print(f"🕒 Время: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Показываем примеры
        if formatted_vacancies:
            print("\n🔍 Примеры вакансий:")
            for i, v in enumerate(formatted_vacancies[:3], 1):
                print(f"{i}. {v['title']}")
                print(f"   {v['company']} - {v['salary']}")
        
    except Exception as e:
        print(f"❌ Ошибка сохранения: {e}")

if __name__ == "__main__":
    main()
