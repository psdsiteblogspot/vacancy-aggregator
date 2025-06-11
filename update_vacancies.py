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
        """Сохранение вакансий в JSON с полной перезаписью"""
        import os
        
        # Определяем путь к файлу
        if 'GITHUB_WORKSPACE' in os.environ:
            filepath = os.path.join(os.environ['GITHUB_WORKSPACE'], filename)
        else:
            filepath = filename
            
        # ВСЕГДА удаляем старый файл перед созданием нового
        if os.path.exists(filepath):
            old_size = os.path.getsize(filepath)
            os.remove(filepath)
            print(f"Старый файл удален (размер был: {old_size} байт)")
        
        # Создаем НОВУЮ структуру данных (без старых данных)
        data = {
            'updated_at': datetime.now().isoformat(),
            'total_count': len(vacancies),
            'status': 'success' if vacancies else 'no_data',
            'source': 'HeadHunter API',
            'note': 'Файл полностью перезаписывается при каждом обновлении',
            'vacancies': vacancies
        }
        
        try:
            # Создаем полностью новый файл
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            # Проверяем результат
            if os.path.exists(filepath):
                new_size = os.path.getsize(filepath)
                print(f"НОВЫЙ файл создан: {filepath}")
                print(f"Размер: {new_size} байт")
                print(f"Содержит: {len(vacancies)} вакансий")
                return True
            else:
                print("ОШИБКА: Файл не был создан!")
                return False
                
        except Exception as e:
            print(f"Ошибка при сохранении файла: {e}")
            return False
    
    def load_existing_data(self, filename='hh_vacancies.json'):
        """Загрузка существующих данных - НЕ ИСПОЛЬЗУЕТСЯ при полной перезаписи"""
        # При полной перезаписи мы НЕ загружаем старые данные
        print("Режим полной перезаписи: старые данные НЕ загружаются")
        return None
    
    def run_update(self):
        """Основной метод обновления - ПОЛНАЯ ПЕРЕЗАПИСЬ"""
        print("=== РЕЖИМ ПОЛНОЙ ПЕРЕЗАПИСИ ДАННЫХ ===")
        print("Старые данные будут полностью удалены!")
        print(f"Время запуска: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Получаем НОВЫЕ вакансии (без объединения со старыми)
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
        
        print(f"\nИтого уникальных НОВЫХ вакансий: {len(unique_vacancies)}")
        
        if not unique_vacancies:
            print("ВНИМАНИЕ: Не получено новых вакансий")
            print("Создаем пустой файл...")
            unique_vacancies = []
        
        # СОХРАНЯЕМ ТОЛЬКО НОВЫЕ ДАННЫЕ (без старых)
        success = self.save_to_json(unique_vacancies)
        
        if success:
            print("=== ПОЛНАЯ ПЕРЕЗАПИСЬ ЗАВЕРШЕНА УСПЕШНО! ===")
            print(f"Файл содержит {len(unique_vacancies)} вакансий")
            return True
        else:
            print("ОШИБКА при сохранении данных")
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
