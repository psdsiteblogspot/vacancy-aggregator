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
        Получение вакансий с HeadHunter API за последние 24 часа
        
        Args:
            text: поисковый запрос
            area: регион (113 - Россия)
            schedule: график работы (remote, fullDay, etc.)
            salary_from: минимальная зарплата
            per_page: количество вакансий на странице (макс 100)
        """
        
        # Базовые параметры запроса - точно как в ссылке HH
        params = {
            'text': text,
            'area': area,
            'search_field': 'name',
            'order_by': 'salary_desc',  # Сортировка по зарплате
            'search_period': 1,  # За последний день (24 часа)
            'per_page': min(per_page, 100),  # Максимум 100
            'page': 0,
            'enable_snippets': 'false'
        }
        
        # Добавляем опциональные параметры только если они заданы
        if schedule == "remote":
            params['schedule'] = 'remote'
            
        if salary_from:
            params['salary'] = salary_from
            
        all_vacancies = []
        page = 0
        max_pages = 10  # Увеличиваем до 10 страниц для получения больше вакансий
        
        print(f"Поиск вакансий: '{text}' в регионе {area} за последние 24 часа")
        print(f"Параметры поиска: {params}")
        
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
                total_found = data.get('found', 0)
                total_pages = data.get('pages', 1)
                
                print(f"Получено {len(vacancies)} вакансий на странице {page + 1}")
                print(f"Всего найдено: {total_found}, всего страниц: {total_pages}")
                
                if not vacancies:
                    print("Больше вакансий нет")
                    break
                    
                # Обрабатываем каждую вакансию
                for vacancy in vacancies:
                    processed_vacancy = self.process_vacancy(vacancy)
                    if processed_vacancy:
                        all_vacancies.append(processed_vacancy)
                
                # Проверяем есть ли еще страницы
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
                
        print(f"Всего загружено {len(all_vacancies)} уникальных вакансий за последние 24 часа")
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
        """Основной метод обновления - получение ТОЛЬКО актуальных вакансий за 24 часа"""
        print("=== ПОЛУЧЕНИЕ АКТУАЛЬНЫХ ВАКАНСИЙ ЗА 24 ЧАСА ===")
        print(f"Время запуска: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Получаем ТОЛЬКО свежие вакансии за последние 24 часа
        print("\n=== Поиск актуальных вакансий системного администратора ===")
        fresh_vacancies = self.get_vacancies(
            text="Системный администратор",
            area=113  # Россия
        )
        
        print(f"\nПолучено {len(fresh_vacancies)} актуальных вакансий за последние 24 часа")
        
        if not fresh_vacancies:
            print("ВНИМАНИЕ: Не найдено вакансий за последние 24 часа")
            print("Возможные причины:")
            print("- Сегодня не публиковались новые вакансии")
            print("- Проблемы с API HeadHunter")
            fresh_vacancies = []
        else:
            # Сортируем по дате публикации (новые сначала)
            fresh_vacancies.sort(key=lambda x: x.get('published_at', ''), reverse=True)
            print(f"Самая новая вакансия: {fresh_vacancies[0].get('published_date_formatted', 'дата неизвестна')}")
            print(f"Самая старая вакансия: {fresh_vacancies[-1].get('published_date_formatted', 'дата неизвестна')}")
        
        # Сохраняем актуальные данные
        success = self.save_to_json(fresh_vacancies)
        
        if success:
            print("=== ОБНОВЛЕНИЕ ЗАВЕРШЕНО УСПЕШНО! ===")
            print(f"Файл содержит {len(fresh_vacancies)} актуальных вакансий")
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
