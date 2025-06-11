#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import json
from datetime import datetime

def test_hh_api():
    """Простой тест API HeadHunter"""
    
    url = "https://api.hh.ru/vacancies"
    headers = {
        'User-Agent': 'VacancyAggregator/1.0 (gradelift.ru)'
    }
    
    # Самые простые параметры
    params = {
        'text': 'системный администратор',
        'area': 113,  # Россия
        'per_page': 20,
        'page': 0
    }
    
    print("Тестируем API HeadHunter...")
    print(f"URL: {url}")
    print(f"Параметры: {params}")
    
    try:
        response = requests.get(url, params=params, headers=headers, timeout=30)
        
        print(f"Статус: {response.status_code}")
        print(f"Итоговый URL: {response.url}")
        
        if response.status_code == 200:
            data = response.json()
            items = data.get('items', [])
            print(f"Успешно получено {len(items)} вакансий")
            
            # Показываем первую вакансию для проверки
            if items:
                first_vacancy = items[0]
                print(f"\nПример вакансии:")
                print(f"ID: {first_vacancy.get('id')}")
                print(f"Название: {first_vacancy.get('name')}")
                print(f"Компания: {first_vacancy.get('employer', {}).get('name')}")
                print(f"Зарплата: {first_vacancy.get('salary')}")
                
            # Сохраняем результат в простой JSON
            simple_data = {
                'updated_at': datetime.now().isoformat(),
                'total_count': len(items),
                'test_status': 'success',
                'vacancies': []
            }
            
            # Обрабатываем каждую вакансию
            for vacancy in items:
                simple_vacancy = {
                    'id': vacancy.get('id'),
                    'name': vacancy.get('name', ''),
                    'company': vacancy.get('employer', {}).get('name', ''),
                    'url': vacancy.get('alternate_url', ''),
                    'published_at': vacancy.get('published_at', ''),
                    'area': vacancy.get('area', {}).get('name', ''),
                    'salary': vacancy.get('salary')
                }
                simple_data['vacancies'].append(simple_vacancy)
            
            # Сохраняем файл
            with open('hh_vacancies.json', 'w', encoding='utf-8') as f:
                json.dump(simple_data, f, ensure_ascii=False, indent=2)
                
            print(f"Данные сохранены в hh_vacancies.json")
            return True
            
        else:
            print(f"Ошибка API: {response.status_code}")
            print(f"Ответ: {response.text}")
            return False
            
    except Exception as e:
        print(f"Ошибка: {e}")
        return False

if __name__ == "__main__":
    success = test_hh_api()
    exit(0 if success else 1)