#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import json
import os
from datetime import datetime

def get_vacancies():
    """Получение вакансий с минимальными параметрами"""
    
    url = "https://api.hh.ru/vacancies"
    headers = {
        'User-Agent': 'Mozilla/5.0 (compatible; VacancyBot/1.0)'
    }
    
    # Минимальные параметры - только самое необходимое
    params = {
        'text': 'системный администратор',
        'area': '113',  # Россия
        'per_page': '50'  # Не больше 50 за раз
    }
    
    print("Запрашиваем вакансии с HeadHunter...")
    
    try:
        response = requests.get(url, params=params, headers=headers, timeout=30)
        
        print(f"Статус ответа: {response.status_code}")
        print(f"URL запроса: {response.url}")
        
        if response.status_code != 200:
            print(f"Ошибка API: {response.text}")
            return None
            
        data = response.json()
        items = data.get('items', [])
        
        print(f"Получено {len(items)} вакансий")
        
        # Простая обработка данных
        vacancies = []
        for item in items:
            vacancy = {
                'id': item.get('id'),
                'name': item.get('name', ''),
                'company': item.get('employer', {}).get('name', '') if item.get('employer') else '',
                'url': item.get('alternate_url', ''),
                'published_at': item.get('published_at', ''),
                'area': item.get('area', {}).get('name', '') if item.get('area') else '',
                'salary': item.get('salary'),
                'snippet': item.get('snippet', {}),
                'experience': item.get('experience', {}).get('name', '') if item.get('experience') else '',
                'employment': item.get('employment', {}).get('name', '') if item.get('employment') else '',
                'schedule': item.get('schedule', {}).get('name', '') if item.get('schedule') else ''
            }
            
            # Форматируем дату
            if vacancy['published_at']:
                try:
                    pub_date = datetime.fromisoformat(vacancy['published_at'].replace('Z', '+00:00'))
                    vacancy['published_date_formatted'] = pub_date.strftime('%d.%m.%Y %H:%M')
                except:
                    vacancy['published_date_formatted'] = vacancy['published_at']
            
            vacancies.append(vacancy)
        
        return vacancies
        
    except requests.exceptions.Timeout:
        print("Превышен таймаут запроса")
        return None
    except requests.exceptions.RequestException as e:
        print(f"Ошибка сети: {e}")
        return None
    except Exception as e:
        print(f"Неожиданная ошибка: {e}")
        return None

def save_vacancies(vacancies):
    """Сохранение вакансий в JSON"""
    
    # Определяем путь к файлу
    if 'GITHUB_WORKSPACE' in os.environ:
        filepath = os.path.join(os.environ['GITHUB_WORKSPACE'], 'hh_vacancies.json')
    else:
        filepath = 'hh_vacancies.json'
    
    data = {
        'updated_at': datetime.now().isoformat(),
        'total_count': len(vacancies),
        'vacancies': vacancies
    }
    
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"Данные сохранены в {filepath}")
        print(f"Сохранено {len(vacancies)} вакансий")
        return True
        
    except Exception as e:
        print(f"Ошибка сохранения: {e}")
        return False

def main():
    print("=== Обновление вакансий ===")
    print(f"Время: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Получаем вакансии
    vacancies = get_vacancies()
    
    if not vacancies:
        print("Не удалось получить вакансии")
        exit(1)
    
    # Сохраняем
    success = save_vacancies(vacancies)
    
    if success:
        print("Успешно завершено!")
        exit(0)
    else:
        print("Ошибка при сохранении")
        exit(1)

if __name__ == "__main__":
    main()
