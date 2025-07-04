import requests
import json
from datetime import datetime
import time
from typing import List, Dict, Optional

# API HH.ru
BASE_URL = "https://api.hh.ru/vacancies"

# Заголовки для запросов
HEADERS = {
    'User-Agent': 'VacancyParser/1.0 (contact@example.com)'
}

# Задержка между запросами (в секундах)
REQUEST_DELAY = 0.3


def get_vacancies_simple() -> tuple[List[Dict], Dict]:
    """
    Простой сбор ВСЕХ вакансий системного администратора в Москве
    
    Returns:
        Кортеж (список вакансий, статистика)
    """
    print("=" * 60)
    print("СБОР ВАКАНСИЙ: Системный администратор в Москве")
    print(f"Время начала: {datetime.now()}")
    print("=" * 60)
    
    params = {
        'text': 'системный администратор',
        'area': '1',  # Только Москва
        'search_field': 'name',  # Поиск в названии
        'per_page': 100,  # Максимум на страницу
        'page': 0
    }
    
    all_vacancies = []
    page = 0
    stats = {
        'found': 0,
        'pages': 0,
        'collected': 0,
        'pages_processed': 0
    }
    
    while True:
        params['page'] = page
        print(f"\n📄 Запрашиваем страницу {page}...")
        
        try:
            # Делаем запрос
            response = requests.get(BASE_URL, params=params, headers=HEADERS, timeout=30)
            
            # Проверяем статус
            if response.status_code != 200:
                print(f"❌ Ошибка HTTP: {response.status_code}")
                print(f"Ответ: {response.text[:500]}")
                break
            
            # Парсим JSON
            data = response.json()
            
            # На первой странице сохраняем общую информацию
            if page == 0:
                stats['found'] = data.get('found', 0)
                stats['pages'] = data.get('pages', 0)
                
                print(f"\n📊 РЕЗУЛЬТАТЫ ПОИСКА:")
                print(f"   Найдено вакансий: {stats['found']}")
                print(f"   Количество страниц: {stats['pages']}")
                print(f"   Альтернативный URL: {data.get('alternate_url', 'не указан')}")
                
                # Диагностика
                max_available = min(stats['pages'] * 100, 2000)
                print(f"   Максимум доступно через API: {max_available}")
                
                if stats['found'] > 2000:
                    print(f"\n⚠️ ВНИМАНИЕ: Найдено {stats['found']} вакансий, но API вернет максимум 2000!")
            
            # Получаем вакансии со страницы
            items = data.get('items', [])
            items_count = len(items)
            
            if items_count == 0:
                print(f"   Страница {page}: пустая, завершаем сбор")
                break
            
            all_vacancies.extend(items)
            stats['collected'] = len(all_vacancies)
            stats['pages_processed'] = page + 1
            
            print(f"   Страница {page}: получено {items_count} вакансий")
            print(f"   Всего собрано: {stats['collected']}")
            
            # Проверяем, есть ли еще страницы
            if page >= stats['pages'] - 1:
                print(f"\n✅ Достигнута последняя страница")
                break
            
            # Проверка лимита API
            if stats['collected'] >= 2000:
                print(f"\n⚠️ Достигнут лимит API в 2000 результатов")
                break
            
            # Проверка на странный случай
            if page >= 19:  # 20 страниц * 100 = 2000
                print(f"\n⚠️ Достигнут лимит в 20 страниц")
                break
            
            page += 1
            time.sleep(REQUEST_DELAY)
            
        except requests.exceptions.RequestException as e:
            print(f"\n❌ Ошибка сети: {e}")
            break
        except json.JSONDecodeError as e:
            print(f"\n❌ Ошибка парсинга JSON: {e}")
            print(f"Ответ: {response.text[:500]}")
            break
        except Exception as e:
            print(f"\n❌ Неожиданная ошибка: {e}")
            import traceback
            traceback.print_exc()
            break
    
    return all_vacancies, stats


def parse_vacancy(item: Dict) -> Dict:
    """Парсит данные одной вакансии"""
    vacancy = {
        'id': item.get('id', ''),
        'title': item.get('name', ''),
        'company': item.get('employer', {}).get('name', ''),
        'company_url': item.get('employer', {}).get('alternate_url', ''),
        'salary': 'не указана',
        'experience': item.get('experience', {}).get('name', ''),
        'schedule': item.get('schedule', {}).get('name', ''),
        'employment': item.get('employment', {}).get('name', ''),
        'area': item.get('area', {}).get('name', ''),
        'publishDate': item.get('published_at', '')[:10],
        'url': item.get('alternate_url', ''),
        'requirement': item.get('snippet', {}).get('requirement', ''),
        'responsibility': item.get('snippet', {}).get('responsibility', '')
    }
    
    # Обработка зарплаты
    if item.get('salary'):
        salary_data = item['salary']
        salary_from = salary_data.get('from')
        salary_to = salary_data.get('to')
        currency = salary_data.get('currency', 'RUR')
        gross = salary_data.get('gross', False)
        
        if salary_from and salary_to:
            vacancy['salary'] = f"от {salary_from:,} до {salary_to:,} {currency}"
        elif salary_from:
            vacancy['salary'] = f"от {salary_from:,} {currency}"
        elif salary_to:
            vacancy['salary'] = f"до {salary_to:,} {currency}"
            
        if gross:
            vacancy['salary'] += " (до вычета налогов)"
        else:
            vacancy['salary'] += " (на руки)"
    
    return vacancy


def analyze_results(vacancies: List[Dict], stats: Dict):
    """Анализирует результаты сбора"""
    print("\n" + "=" * 60)
    print("АНАЛИЗ РЕЗУЛЬТАТОВ")
    print("=" * 60)
    
    print(f"\n📊 Основные показатели:")
    print(f"   Найдено в поиске: {stats['found']}")
    print(f"   Собрано фактически: {stats['collected']}")
    print(f"   Страниц обработано: {stats['pages_processed']} из {stats['pages']}")
    
    if stats['found'] > 0:
        completeness = (stats['collected'] / stats['found']) * 100
        print(f"   Полнота сбора: {completeness:.1f}%")
        
        missing = stats['found'] - stats['collected']
        if missing > 0:
            print(f"   Не собрано: {missing} вакансий")
            
            print(f"\n❓ Возможные причины потери {missing} вакансий:")
            
            if stats['found'] > 2000:
                print(f"   1. Превышен лимит API в 2000 результатов (найдено {stats['found']})")
            
            if stats['pages_processed'] < stats['pages']:
                print(f"   2. Обработаны не все страницы ({stats['pages_processed']} из {stats['pages']})")
            
            if completeness > 95:
                print(f"   3. Небольшие расхождения могут быть из-за изменений в базе во время сбора")
            else:
                print(f"   3. Проверьте параметры поиска - возможно, они отличаются от сайта")
                print(f"   4. Проверьте наличие ошибок сети или таймаутов")
    
    # Анализ по графикам работы
    if vacancies:
        schedules = {}
        for v in vacancies:
            schedule = v.get('schedule', 'Не указан')
            schedules[schedule] = schedules.get(schedule, 0) + 1
        
        print(f"\n📅 Распределение по графику работы:")
        for schedule, count in sorted(schedules.items(), key=lambda x: x[1], reverse=True):
            percent = (count / len(vacancies)) * 100
            print(f"   {schedule}: {count} ({percent:.1f}%)")


def save_vacancies(vacancies: List[Dict], stats: Dict, filename: str = 'hh_vacancies_moscow.json'):
    """Сохраняет вакансии в JSON файл"""
    # Парсим вакансии
    parsed_vacancies = [parse_vacancy(v) for v in vacancies]
    
    output = {
        'source': 'hh.ru',
        'search_params': {
            'text': 'системный администратор',
            'area': 'Москва',
            'area_id': '1',
            'search_field': 'В названии вакансии',
            'filter': 'БЕЗ дополнительных фильтров'
        },
        'updated': datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ'),
        'statistics': {
            'found': stats['found'],
            'collected': stats['collected'],
            'completeness': f"{(stats['collected'] / stats['found'] * 100):.1f}%" if stats['found'] > 0 else "0%",
            'pages_processed': stats['pages_processed'],
            'total_pages': stats['pages']
        },
        'total_count': len(parsed_vacancies),
        'vacancies': parsed_vacancies
    }
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 Файл {filename} успешно создан!")


def main():
    """Основная функция программы"""
    try:
        # Собираем вакансии
        raw_vacancies, stats = get_vacancies_simple()
        
        if not raw_vacancies:
            print("\n❌ Не удалось собрать вакансии")
            return
        
        # Анализируем результаты
        analyze_results(raw_vacancies, stats)
        
        # Сохраняем
        save_vacancies(raw_vacancies, stats)
        
        print("\n✅ Готово!")
        
    except KeyboardInterrupt:
        print("\n\n⚠️ Сбор вакансий прерван пользователем")
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
