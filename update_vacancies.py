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
            'User-Agent': 'VacancyAggregator/1.0 (gradelift.ru)',
            'HH-User-Agent': 'VacancyAggregator/1.0 (gradelift.ru)'
        }
        self.vacancies = []
        
    def get_vacancies(self, text="Системный администратор", area=113, 
                     schedule=None, salary_from=None, per_page=100):
        """
        Получение вакансий с HeadHunter API
        
        Args:
            text: поисковый запрос
            area: регион (113 - Россия)
            schedule: график работы (remote, fullDay, etc.)
            salary_from: минимальная зарплата
            per_page: количество вакансий на странице (макс 100)
        """
        
        # Базовые параметры запроса
        params = {
            'text': text,
            'area': area,
            'search_field': 'name',
            'order_by': 'salary_desc',
            'search_period': 1,  # За последний день
            'per_page': min(per_page, 100),  # Максимум 100
            'page': 0
        }
        
        # Добавляем опциональные параметры только если они заданы
        if schedule:
            params['schedule'] = schedule
            
        if salary_from:
            params['salary'] = salary_from
            
        all_vacancies = []
        page = 0
        max_pages = 5  # Ограничиваем количество страниц
        
        print(f"Поиск вакансий: '{text}' в регионе {area}")
        
        while page < max_pages:
            params['page'] = page
            
            try:
                print(f"Загружаем страницу {page + 1}...")
                
                # Делаем запрос к API
                response = requests.get(self.base_url, params=params, headers=self.headers, timeout=30)
                
                print(f"URL запроса: {response.url}")
                print(f"Статус ответа: {response.status_code}")
                
                if response.status_code == 400:
                    print(f"Ошибка 400: {response.text}")
                    break
                    
                response.raise_for_status()
                
                data = response.json()
                vacancies = data.get('items', [])
                
                print(f"Получено {len(vacancies)} вакансий на странице {page + 1}")
                
                if not vacancies:
                    print("Больше вакансий нет")
                    break
                    
                # Обрабатываем каждую вакансию
                for vacancy in vacancies:
                    processed_vacancy = self.process_vacancy(vacancy)
                    if processed_vacancy:
                        all_vacancies.append(processed_vacancy)
                
                # Проверяем есть ли еще страницы
                total_pages = data.get('pages', 1)
                print(f"Всего страниц: {total_pages}")
                
                if page >= total_pages - 1:
                    print("Достигнута последняя страница")
                    break
                    
                page += 1
                
                # Пауза между запросами для соблюдения лимитов API
                time.sleep(1)
                
            except requests.exceptions.Timeout:
                print("Превышен таймаут запроса")
                break
            except requests.exceptions.RequestException as e:
                print(f"Ошибка при запросе к API: {e}")
                break
            except Exception as e:
                print(f"Неожиданная ошибка: {e}")
                break
                
        print(f"Всего загружено {len(all_vacancies)} вакансий")
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
        
        # Получаем новые вакансии с разными параметрами
        print("\n=== Поиск удаленных вакансий системного администратора ===")
        remote_vacancies = self.get_vacancies(
            text="Системный администратор",
            area=113,  # Россия
            schedule="remote"  # Удаленная работа
        )
        
        print(f"\n=== Поиск всех вакансий системного администратора ===")
        all_vacancies = self.get_vacancies(
            text="Системный администратор",
            area=113  # Россия, без ограничения по типу работы
        )
        
        # Объединяем результаты и убираем дубликаты
        combined_vacancies = remote_vacancies + all_vacancies
        
        # Удаляем дубликаты по ID
        unique_vacancies = []
        seen_ids = set()
        
        for vacancy in combined_vacancies:
            if vacancy['id'] not in seen_ids:
                unique_vacancies.append(vacancy)
                seen_ids.add(vacancy['id'])
        
        print(f"\nИтого уникальных вакансий: {len(unique_vacancies)}")
        
        if not unique_vacancies:
            print("Не удалось получить новые вакансии")
            return False
        
        # Загружаем существующие данные
        existing_data = self.load_existing_data()
        
        if existing_data:
            existing_ids = {v['id'] for v in existing_data.get('vacancies', [])}
            # Фильтруем только новые вакансии
            really_new = [v for v in unique_vacancies if v['id'] not in existing_ids]
            
            if really_new:
                print(f"Найдено {len(really_new)} действительно новых вакансий")
                # Объединяем с существующими (новые в начале)
                all_vacancies_final = really_new + existing_data.get('vacancies', [])
                
                # Ограничиваем общее количество (например, последние 500)
                all_vacancies_final = all_vacancies_final[:500]
            else:
                print("Новых вакансий не найдено, используем существующие данные")
                all_vacancies_final = existing_data.get('vacancies', [])
        else:
            all_vacancies_final = unique_vacancies
        
        # Сохраняем обновленные данные
        success = self.save_to_json(all_vacancies_final)
        
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
