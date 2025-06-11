#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import json
import time
from datetime import datetime, timedelta
import re
from urllib.parse import urlencode, parse_qs, urlparse

class VacancyAggregator:
    def __init__(self):
        self.base_url = "https://api.hh.ru/vacancies"
        self.headers = {
            'User-Agent': 'VacancyAggregator/1.0 (your-email@example.com)'
        }
        self.vacancies = []
        
    def get_vacancies(self, text="Системный администратор", area=113, 
                     work_format="REMOTE", salary_from=None, per_page=100):
        """
        Получение вакансий с HeadHunter API
        
        Args:
            text: поисковый запрос
            area: регион (113 - Россия)
            work_format: формат работы (REMOTE, FULL_TIME, etc.)
            salary_from: минимальная зарплата
            per_page: количество вакансий на странице (макс 100)
        """
        
        params = {
            'text': text,
            'area': area,
            'search_field': 'name',
            'order_by': 'salary_desc',
            'search_period': 1,  # За последний день
            'per_page': per_page,
            'page': 0
        }
        
        if work_format:
            params['schedule'] = work_format
            
        if salary_from:
            params['salary_from'] = salary_from
            
        all_vacancies = []
        page = 0
        
        while True:
            params['page'] = page
            
            try:
                print(f"Загружаем страницу {page + 1}...")
                response = requests.get(self.base_url, params=params, headers=self.headers)
                response.raise_for_status()
                
                data = response.json()
                vacancies = data.get('items', [])
                
                if not vacancies:
                    break
                    
                # Обрабатываем каждую вакансию
                for vacancy in vacancies:
                    processed_vacancy = self.process_vacancy(vacancy)
                    if processed_vacancy:
                        all_vacancies.append(processed_vacancy)
                
                # Проверяем есть ли еще страницы
                if page >= data.get('pages', 1) - 1:
                    break
                    
                page += 1
                
                # Пауза между запросами
                time.sleep(0.5)
                
            except requests.exceptions.RequestException as e:
                print(f"Ошибка при запросе к API: {e}")
                break
            except Exception as e:
                print(f"Неожиданная ошибка: {e}")
                break
                
        return all_vacancies
    
    def process_vacancy(self, vacancy):
        """Обработка одной вакансии"""
        try:
            # Извлекаем основную информацию
            processed = {
                'id': vacancy.get('id'),
                'name': vacancy.get('name', ''),
                'company': vacancy.get('employer', {}).get('name', ''),
                'company_url': vacancy.get('employer', {}).get('alternate_url', ''),
                'url': vacancy.get('alternate_url', ''),
                'published_at': vacancy.get('published_at', ''),
                'created_at': vacancy.get('created_at', ''),
                'area': vacancy.get('area', {}).get('name', ''),
                'experience': vacancy.get('experience', {}).get('name', ''),
                'employment': vacancy.get('employment', {}).get('name', ''),
                'schedule': vacancy.get('schedule', {}).get('name', ''),
                'snippet': {
                    'requirement': vacancy.get('snippet', {}).get('requirement', ''),
                    'responsibility': vacancy.get('snippet', {}).get('responsibility', '')
                }
            }
            
            # Обрабатываем зарплату
            salary = vacancy.get('salary')
            if salary:
                processed['salary'] = {
                    'from': salary.get('from'),
                    'to': salary.get('to'),
                    'currency': salary.get('currency', 'RUR'),
                    'gross': salary.get('gross', False)
                }
            else:
                processed['salary'] = None
                
            # Форматируем дату для отображения
            if processed['published_at']:
                try:
                    pub_date = datetime.fromisoformat(processed['published_at'].replace('Z', '+00:00'))
                    processed['published_date_formatted'] = pub_date.strftime('%d.%m.%Y %H:%M')
                except:
                    processed['published_date_formatted'] = processed['published_at']
            
            return processed
            
        except Exception as e:
            print(f"Ошибка при обработке вакансии {vacancy.get('id', 'unknown')}: {e}")
            return None
    
    def save_to_json(self, vacancies, filename='hh_vacancies.json'):
        """Сохранение вакансий в JSON файл"""
        import os
        
        # Убеждаемся что сохраняем в корневую папку проекта
        if 'GITHUB_WORKSPACE' in os.environ:
            filepath = os.path.join(os.environ['GITHUB_WORKSPACE'], filename)
        else:
            filepath = filename
            
        data = {
            'updated_at': datetime.now().isoformat(),
            'total_count': len(vacancies),
            'vacancies': vacancies
        }
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"Сохранено {len(vacancies)} вакансий в файл {filepath}")
            return True
        except Exception as e:
            print(f"Ошибка при сохранении файла: {e}")
            return False
    
    def load_existing_data(self, filename='hh_vacancies.json'):
        """Загрузка существующих данных"""
        import os
        
        # Убеждаемся что читаем из правильного места
        if 'GITHUB_WORKSPACE' in os.environ:
            filepath = os.path.join(os.environ['GITHUB_WORKSPACE'], filename)
        else:
            filepath = filename
            
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"Файл {filepath} не найден, создаем новый")
            return None
        except Exception as e:
            print(f"Ошибка при загрузке файла: {e}")
            return None
    
    def run_update(self):
        """Основной метод обновления"""
        print("Начинаем обновление вакансий...")
        print(f"Время запуска: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Получаем новые вакансии
        new_vacancies = self.get_vacancies()
        
        if not new_vacancies:
            print("Не удалось получить новые вакансии")
            return False
        
        print(f"Получено {len(new_vacancies)} новых вакансий")
        
        # Загружаем существующие данные
        existing_data = self.load_existing_data()
        
        if existing_data:
            existing_ids = {v['id'] for v in existing_data.get('vacancies', [])}
            # Фильтруем только новые вакансии
            really_new = [v for v in new_vacancies if v['id'] not in existing_ids]
            
            if really_new:
                print(f"Найдено {len(really_new)} действительно новых вакансий")
                # Объединяем с существующими (новые в начале)
                all_vacancies = really_new + existing_data.get('vacancies', [])
                
                # Ограничиваем общее количество (например, последние 1000)
                all_vacancies = all_vacancies[:1000]
            else:
                print("Новых вакансий не найдено")
                all_vacancies = existing_data.get('vacancies', [])
        else:
            all_vacancies = new_vacancies
        
        # Сохраняем обновленные данные
        success = self.save_to_json(all_vacancies)
        
        if success:
            print("Обновление завершено успешно!")
            return True
        else:
            print("Ошибка при сохранении данных")
            return False

def main():
    aggregator = VacancyAggregator()
    
    try:
        success = aggregator.run_update()
        if success:
            exit(0)
        else:
            exit(1)
    except Exception as e:
        print(f"Критическая ошибка: {e}")
        exit(1)

if __name__ == "__main__":
    main()
