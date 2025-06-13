import requests
import json
from datetime import datetime
import time
from typing import List, Dict, Optional

# API HH.ru
BASE_URL = "https://api.hh.ru/vacancies"

# Параметры поиска
SEARCH_PARAMS = {
    'text': 'системный администратор',  # Ключевые слова
    'area': ['80', '81', '82', '83', '84', '85', '86', '87', '88', '89', '90', '91', '92', '93', '94', '95', '96', '97', '98', '99', '100', '101', '102', '103', '104'],                        # Регионы
    'schedule': ['remote', 'flexible', 'fullDay', 'shift', 'flyInFlyOut'],               # Удаленная работа
    'search_field': 'name',             # Искать только в названии вакансии
    'per_page': 1000,                    # Максимум вакансий на страницу
    'page': 0
}

# Заголовки для запросов
HEADERS = {
    'User-Agent': 'VacancyParser/1.0 (contact@example.com)'  # Более информативный User-Agent
}

# Задержка между запросами (в секундах)
REQUEST_DELAY = 0.5


def get_vacancies_page(page: int) -> Optional[Dict]:
    """
    Получает одну страницу вакансий из API HH.ru
    
    Args:
        page: Номер страницы
        
    Returns:
        Словарь с данными или None в случае ошибки
    """
    params = SEARCH_PARAMS.copy()
    params['page'] = page
    
    try:
        response = requests.get(BASE_URL, params=params, headers=HEADERS)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Ошибка при запросе страницы {page}: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"Ошибка при разборе JSON на странице {page}: {e}")
        return None


def parse_vacancy(item: Dict) -> Dict:
    """
    Парсит данные одной вакансии
    
    Args:
        item: Словарь с данными вакансии из API
        
    Returns:
        Отформатированный словарь с данными вакансии
    """
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
        'publishDate': item.get('published_at', '')[:10],  # Только дата
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
            
        # Добавляем информацию о типе зарплаты
        if gross:
            vacancy['salary'] += " (до вычета налогов)"
        else:
            vacancy['salary'] += " (на руки)"
    
    return vacancy


def collect_all_vacancies() -> List[Dict]:
    """
    Собирает все вакансии со всех страниц
    
    Returns:
        Список всех найденных вакансий
    """
    all_vacancies = []
    page = 0
    total_pages = None
    
    print("Начинаем сбор вакансий...")
    print(f"Параметры поиска:")
    print(f"  - Текст: '{SEARCH_PARAMS['text']}'")
    print(f"  - Регион: Россия")
    print(f"  - Формат работы: Удалённо")
    print(f"  - Поиск в: названии вакансии")
    print("-" * 50)
    
    while True:
        # Получаем страницу
        data = get_vacancies_page(page)
        
        if data is None:
            print(f"Не удалось получить страницу {page}. Пропускаем...")
            page += 1
            continue
        
        # На первой странице узнаем общее количество
        if total_pages is None:
            total_pages = data.get('pages', 0)
            total_found = data.get('found', 0)
            print(f"Найдено вакансий: {total_found}")
            print(f"Страниц для обработки: {total_pages}")
            print("-" * 50)
        
        # Обрабатываем вакансии на странице
        items = data.get('items', [])
        for item in items:
            vacancy = parse_vacancy(item)
            all_vacancies.append(vacancy)
        
        # Выводим прогресс
        print(f"Обработано страниц: {page + 1}/{total_pages} | Собрано вакансий: {len(all_vacancies)}")
        
        # Проверяем, есть ли еще страницы
        page += 1
        if page >= total_pages:
            break
        
        # Задержка между запросами
        time.sleep(REQUEST_DELAY)
    
    return all_vacancies


def save_vacancies(vacancies: List[Dict], filename: str = 'hh_vacancies_fullDay.json'):
    """
    Сохраняет вакансии в JSON файл
    
    Args:
        vacancies: Список вакансий
        filename: Имя файла для сохранения
    """
    output = {
        'source': 'hh.ru',
        'search_params': {
            'text': SEARCH_PARAMS['text'],
            'area': 'Россия',
            'schedule': 'Удалённая работа',
            'search_field': 'В названии вакансии'
        },
        'updated': datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ'),
        'total_count': len(vacancies),
        'vacancies': vacancies
    }
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ Файл {filename} успешно создан!")
    print(f"📊 Всего сохранено вакансий: {len(vacancies)}")


def print_statistics(vacancies: List[Dict]):
    """
    Выводит статистику по собранным вакансиям
    
    Args:
        vacancies: Список вакансий
    """
    print("\n📈 Статистика по вакансиям:")
    print("-" * 50)
    
    # Топ компаний
    companies = {}
    for v in vacancies:
        company = v['company']
        companies[company] = companies.get(company, 0) + 1
    
    top_companies = sorted(companies.items(), key=lambda x: x[1], reverse=True)[:10]
    print("\n🏢 Топ-10 компаний по количеству вакансий:")
    for i, (company, count) in enumerate(top_companies, 1):
        print(f"{i:2d}. {company}: {count} вакансий")
    
    # Статистика по зарплатам
    with_salary = sum(1 for v in vacancies if v['salary'] != 'не указана')
    print(f"\n💰 Вакансий с указанной зарплатой: {with_salary} ({with_salary/len(vacancies)*100:.1f}%)")
    
    # Статистика по регионам
    regions = {}
    for v in vacancies:
        region = v['area']
        regions[region] = regions.get(region, 0) + 1
    
    top_regions = sorted(regions.items(), key=lambda x: x[1], reverse=True)[:10]
    print("\n🌍 Топ-10 регионов:")
    for i, (region, count) in enumerate(top_regions, 1):
        print(f"{i:2d}. {region}: {count} вакансий")


def main():
    """
    Основная функция программы
    """
    try:
        # Собираем все вакансии
        vacancies = collect_all_vacancies()
        
        if not vacancies:
            print("❌ Не удалось найти ни одной вакансии")
            return
        
        # Сохраняем результаты
        save_vacancies(vacancies)
        
        # Выводим статистику
        print_statistics(vacancies)
        
    except KeyboardInterrupt:
        print("\n\n⚠️ Сбор вакансий прерван пользователем")
    except Exception as e:
        print(f"\n❌ Произошла ошибка: {e}")


if __name__ == "__main__":
    main()
