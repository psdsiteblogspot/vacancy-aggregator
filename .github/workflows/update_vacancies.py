#!/usr/bin/env python3
"""
Скрипт для получения вакансий системных администраторов с HeadHunter API
Использует точные параметры поиска как на сайте hh.ru
API HeadHunter не требует ключа для базовых запросов
"""

import json
import requests
import time
from datetime import datetime
from urllib.parse import quote

class HeadHunterParser:
    def __init__(self):
        self.base_url = "https://api.hh.ru"
        self.headers = {
            'User-Agent': 'VacancyAggregator/1.0 (gradelift.ru)'
        }
        
    def search_vacancies(self, text="Системный администратор", area="113", work_format="remote"):
        """
        Поиск вакансий через API HeadHunter с параметрами как на сайте
        
        Args:
            text: поисковый запрос
            area: регион (113 = Россия)
            work_format: формат работы (remote = удаленная работа)
        """
        
        # Параметры точно как в вашей ссылке
        params = {
            'text': text,
            'area': area,  # 113 = Россия
            'search_field': 'name',  # Поиск по названию вакансии
            'per_page': 100,  # Максимум вакансий на страницу
            'page': 0,
            'order_by': 'salary_desc',  # Сортировка по зарплате по убыванию
            'search_period': 1,  # За последний день
            'only_with_salary': 'true',  # Только с указанной зарплатой
            'currency': 'RUR'
        }
        
        # Добавляем удаленную работу если указано
        if work_format == "remote":
            params['schedule'] = 'remote'
            
        try:
            print(f"🔍 Поиск вакансий: '{text}' в регионе {area}")
            print(f"📋 Параметры: {params}")
            
            response = requests.get(
                f"{self.base_url}/vacancies",
                params=params,
                headers=self.headers,
                timeout=15
            )
            
            print(f"🌐 URL запроса: {response.url}")
            
            if response.status_code == 200:
                data = response.json()
                total_found = data.get('found', 0)
                items = data.get('items', [])
                
                print(f"✅ Всего найдено: {total_found} вакансий")
                print(f"📄 Получено на странице: {len(items)} вакансий")
                
                return {
                    'items': items,
                    'total_found': total_found,
                    'pages': data.get('pages', 1),
                    'per_page': data.get('per_page', 100)
                }
            else:
                print(f"❌ Ошибка API: {response.status_code}")
                print(f"📝 Ответ: {response.text[:500]}...")
                return {'items': [], 'total_found': 0}
                
        except requests.RequestException as e:
            print(f"❌ Ошибка сети: {e}")
            return {'items': [], 'total_found': 0}
    
    def get_multiple_pages(self, text="Системный администратор", max_pages=5):
        """Получение нескольких страниц результатов"""
        all_items = []
        
        # Первый запрос для получения общей информации
        first_result = self.search_vacancies(text=text)
        all_items.extend(first_result['items'])
        
        total_pages = min(first_result.get('pages', 1), max_pages)
        total_found = first_result.get('total_found', 0)
        
        print(f"📊 Всего страниц: {total_pages}, найдено вакансий: {total_found}")
        
        # Запросы дополнительных страниц
        for page in range(1, total_pages):
            print(f"📄 Загружаем страницу {page + 1}/{total_pages}")
            
            params = {
                'text': text,
                'area': '113',  # Россия
                'search_field': 'name',
                'per_page': 100,
                'page': page,
                'order_by': 'salary_desc',
                'search_period': 1,
                'only_with_salary': 'true',
                'schedule': 'remote',
                'currency': 'RUR'
            }
            
            try:
                response = requests.get(
                    f"{self.base_url}/vacancies",
                    params=params,
                    headers=self.headers,
                    timeout=15
                )
                
                if response.status_code == 200:
                    data = response.json()
                    items = data.get('items', [])
                    all_items.extend(items)
                    print(f"✅ Страница {page + 1}: добавлено {len(items)} вакансий")
                else:
                    print(f"❌ Ошибка на странице {page + 1}: {response.status_code}")
                    
            except Exception as e:
                print(f"❌ Ошибка при загрузке страницы {page + 1}: {e}")
            
            # Пауза между запросами
            time.sleep(0.5)
        
        return {
            'items': all_items,
            'total_found': total_found,
            'pages_loaded': len(all_items) // 100 + (1 if len(all_items) % 100 else 0)
        }
    
    def format_salary(self, salary_data):
        """Форматирование зарплаты"""
        if not salary_data:
            return "Зарплата не указана"
            
        salary_from = salary_data.get('from')
        salary_to = salary_data.get('to')
        currency = salary_data.get('currency', 'RUR')
        gross = salary_data.get('gross', True)
        
        currency_symbol = {
            'RUR': 'руб.',
            'USD': '$',
            'EUR': '€',
            'KZT': 'тенге',
            'UZS': 'сум'
        }.get(currency, currency)
        
        gross_text = "" if gross else " на руки"
        
        if salary_from and salary_to:
            return f"от {salary_from:,} до {salary_to:,} {currency_symbol}{gross_text}".replace(',', ' ')
        elif salary_from:
            return f"от {salary_from:,} {currency_symbol}{gross_text}".replace(',', ' ')
        elif salary_to:
            return f"до {salary_to:,} {currency_symbol}{gross_text}".replace(',', ' ')
        else:
            return "Зарплата не указана"
    
    def format_vacancy(self, vacancy):
        """Форматирование данных вакансии"""
        published_date = vacancy.get('published_at', '')
        if published_date:
            # Преобразуем формат даты
            try:
                dt = datetime.fromisoformat(published_date.replace('Z', '+00:00'))
                formatted_date = dt.strftime('%Y-%m-%d')
            except:
                formatted_date = published_date[:10]
        else:
            formatted_date = ''
            
        return {
            'id': vacancy.get('id'),
            'title': vacancy.get('name', 'Без названия'),
            'company': vacancy.get('employer', {}).get('name', 'Компания не указана'),
            'salary': self.format_salary(vacancy.get('salary')),
            'publishDate': formatted_date,
            'url': vacancy.get('alternate_url', ''),
            'area': vacancy.get('area', {}).get('name', ''),
            'experience': vacancy.get('experience', {}).get('name', ''),
            'employment': vacancy.get('employment', {}).get('name', ''),
            'schedule': vacancy.get('schedule', {}).get('name', ''),
            'premium': vacancy.get('premium', False),
            'has_test': vacancy.get('has_test', False),
            'response_letter_required': vacancy.get('response_letter_required', False)
        }

def main():
    print("🚀 Запуск обновления вакансий с HeadHunter API...")
    print("📅 Используются параметры поиска как на сайте hh.ru")
    
    parser = HeadHunterParser()
    
    # Поисковые запросы с высокими зарплатами для системных администраторов
    search_queries = [
        "Системный администратор",
        "DevOps engineer", 
        "Senior системный администратор",
        "Ведущий системный администратор",
        "Старший системный администратор"
    ]
    
    all_vacancies = []
    search_stats = {}
    
    for query in search_queries:
        print(f"\n{'='*50}")
        print(f"🔍 Поиск по запросу: {query}")
        print(f"{'='*50}")
        
        # Получаем несколько страниц результатов
        result = parser.get_multiple_pages(text=query, max_pages=3)
        
        if result['items']:
            formatted_vacancies = [parser.format_vacancy(v) for v in result['items']]
            all_vacancies.extend(formatted_vacancies)
            search_stats[query] = {
                'found': result['total_found'],
                'loaded': len(formatted_vacancies)
            }
            print(f"✅ По запросу '{query}': найдено {result['total_found']}, загружено {len(formatted_vacancies)} вакансий")
        else:
            search_stats[query] = {'found': 0, 'loaded': 0}
            print(f"⚠️  По запросу '{query}': вакансии не найдены")
            
        # Пауза между разными запросами
        time.sleep(1)
    
    # Удаляем дубликаты по ID
    unique_vacancies = []
    seen_ids = set()
    
    for vacancy in all_vacancies:
        if vacancy['id'] and vacancy['id'] not in seen_ids:
            unique_vacancies.append(vacancy)
            seen_ids.add(vacancy['id'])
    
    # Сортируем по дате публикации (новые сначала)
    unique_vacancies.sort(key=lambda x: x['publishDate'], reverse=True)
    
    print(f"\n{'='*50}")
    print(f"📊 ИТОГОВАЯ СТАТИСТИКА")
    print(f"{'='*50}")
    
    for query, stats in search_stats.items():
        print(f"📋 {query}: найдено {stats['found']}, загружено {stats['loaded']}")
    
    print(f"\n📈 Всего обработано: {len(all_vacancies)} вакансий")
    print(f"🎯 Уникальных: {len(unique_vacancies)} вакансий")
    
    # Анализ зарплат
    salaries = []
    for v in unique_vacancies:
        salary_text = v['salary']
        if 'от' in salary_text:
            try:
                # Извлекаем первое число (минимальная зарплата)
                import re
                numbers = re.findall(r'\d+', salary_text.replace(' ', ''))
                if numbers:
                    salaries.append(int(numbers[0]))
            except:
                pass
    
    if salaries:
        avg_salary = sum(salaries) // len(salaries)
        min_salary = min(salaries)
        max_salary = max(salaries)
        print(f"💰 Средняя зарплата: {avg_salary:,} руб.".replace(',', ' '))
        print(f"💰 Диапазон: {min_salary:,} - {max_salary:,} руб.".replace(',', ' '))
    
    # Создаем финальную структуру данных
    result = {
        'source': 'hh.ru',
        'updated': datetime.now().isoformat() + 'Z',
        'search_parameters': {
            'area': '113',  # Россия
            'search_field': 'name',
            'order_by': 'salary_desc',
            'search_period': 1,
            'only_with_salary': True,
            'schedule': 'remote'
        },
        'search_queries': list(search_stats.keys()),
        'statistics': {
            'total_found': sum(s['found'] for s in search_stats.values()),
            'total_loaded': len(all_vacancies),
            'unique_vacancies': len(unique_vacancies),
            'avg_salary': avg_salary if salaries else 0,
            'salary_range': {'min': min_salary, 'max': max_salary} if salaries else None
        },
        'vacancies': unique_vacancies[:100]  # Ограничиваем до 100 лучших вакансий
    }
    
    # Сохраняем в файл
    try:
        with open('hh_vacancies.json', 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        print(f"\n✅ Файл hh_vacancies.json успешно обновлен!")
        print(f"📁 Сохранено {len(result['vacancies'])} вакансий")
        print(f"🕒 Время обновления: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Показываем примеры вакансий
        if result['vacancies']:
            print(f"\n🔍 Примеры найденных вакансий:")
            for i, v in enumerate(result['vacancies'][:3], 1):
                print(f"{i}. {v['title']} - {v['company']} - {v['salary']}")
        
    except Exception as e:
        print(f"❌ Ошибка при сохранении файла: {e}")
        exit(1)

if __name__ == "__main__":
    main()
