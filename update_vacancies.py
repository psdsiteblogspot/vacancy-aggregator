import requests
import json
from datetime import datetime, timedelta
import time
from typing import List, Dict, Optional, Set

# API HH.ru
BASE_URL = "https://api.hh.ru/vacancies"

# Заголовки для запросов
HEADERS = {
    'User-Agent': 'VacancyParser/2.0 (contact@example.com)'
}

# Задержка между запросами
REQUEST_DELAY = 0.3

# Ключевые слова для поиска
SEARCH_KEYWORDS = [
    'системный администратор',
    'сисадмин',
    'system administrator'
]


def get_vacancies_with_pagination_fix(keyword: str, region_id: str = '1') -> tuple[List[Dict], Dict]:
    """
    Получает вакансии с обходом ограничений пагинации
    Использует per_page=50 как на сайте и сегментацию при необходимости
    """
    print(f"\n{'='*60}")
    print(f"🔍 Поиск: '{keyword}' в Москве")
    print(f"{'='*60}")
    
    all_vacancies = []
    stats = {
        'found': 0,
        'collected': 0,
        'method': 'standard'
    }
    
    # Сначала пробуем стандартный метод с per_page=50
    params = {
        'text': keyword,
        'area': region_id,
        'search_field': 'name',
        'per_page': 50,  # Как на сайте!
        'page': 0
    }
    
    # Первый запрос для получения общей информации
    try:
        response = requests.get(BASE_URL, params=params, headers=HEADERS, timeout=30)
        if response.status_code == 200:
            data = response.json()
            stats['found'] = data.get('found', 0)
            total_pages = data.get('pages', 0)
            
            print(f"Найдено: {stats['found']} вакансий")
            print(f"Страниц: {total_pages}")
            
            # Проверяем, нужна ли сегментация
            max_accessible = 20 * 50  # Предполагаем лимит в 20 страниц
            if stats['found'] > max_accessible:
                print(f"⚠️ Требуется сегментация: {stats['found']} > {max_accessible}")
                stats['method'] = 'segmented'
                # Используем сегментацию по датам
                all_vacancies = get_with_date_segmentation(keyword, region_id)
                stats['collected'] = len(all_vacancies)
            else:
                # Стандартный сбор
                all_vacancies = collect_all_pages(params, total_pages)
                stats['collected'] = len(all_vacancies)
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
    
    print(f"✅ Собрано: {stats['collected']} из {stats['found']} ({stats['method']})")
    return all_vacancies, stats


def collect_all_pages(base_params: Dict, total_pages: int) -> List[Dict]:
    """Собирает все доступные страницы"""
    all_items = []
    
    for page in range(min(total_pages, 20)):  # Ограничиваем 20 страницами
        params = base_params.copy()
        params['page'] = page
        
        try:
            response = requests.get(BASE_URL, params=params, headers=HEADERS, timeout=30)
            if response.status_code == 200:
                data = response.json()
                items = data.get('items', [])
                
                if not items:
                    print(f"Страница {page}: пустая, останавливаем")
                    break
                
                all_items.extend(items)
                print(f"Страница {page}: {len(items)} вакансий (всего: {len(all_items)})")
                
                time.sleep(REQUEST_DELAY)
            else:
                print(f"Страница {page}: ошибка {response.status_code}")
                break
                
        except Exception as e:
            print(f"Страница {page}: ошибка {e}")
            break
    
    return all_items


def get_with_date_segmentation(keyword: str, region_id: str) -> List[Dict]:
    """Получает вакансии с сегментацией по датам"""
    print("\n📅 Используем сегментацию по датам публикации")
    
    all_vacancies = []
    unique_ids = set()
    
    # Сегменты по времени (последние 30 дней)
    segments = [
        {'days': 1, 'name': 'За последние 24 часа'},
        {'days': 3, 'name': 'За последние 3 дня'},
        {'days': 7, 'name': 'За последнюю неделю'},
        {'days': 14, 'name': 'За последние 2 недели'},
        {'days': 30, 'name': 'За последний месяц'}
    ]
    
    end_date = datetime.now()
    
    for i, segment in enumerate(segments):
        # Для первого сегмента начинаем с текущего момента
        if i == 0:
            date_from = end_date - timedelta(days=segment['days'])
        else:
            # Для остальных - с конца предыдущего сегмента
            date_from = end_date - timedelta(days=segment['days'])
            date_to_prev = end_date - timedelta(days=segments[i-1]['days'])
            date_from = date_to_prev
        
        date_to = end_date if i == 0 else end_date - timedelta(days=segments[i-1]['days'])
        
        print(f"\n🔍 {segment['name']}")
        print(f"   С {date_from.strftime('%Y-%m-%d')} по {date_to.strftime('%Y-%m-%d')}")
        
        params = {
            'text': keyword,
            'area': region_id,
            'search_field': 'name',
            'date_from': date_from.strftime('%Y-%m-%d'),
            'date_to': date_to.strftime('%Y-%m-%d'),
            'per_page': 50,
            'page': 0
        }
        
        # Собираем вакансии для сегмента
        segment_vacancies = []
        page = 0
        
        while True:
            params['page'] = page
            
            try:
                response = requests.get(BASE_URL, params=params, headers=HEADERS, timeout=30)
                if response.status_code == 200:
                    data = response.json()
                    
                    if page == 0:
                        found_in_segment = data.get('found', 0)
                        print(f"   Найдено в сегменте: {found_in_segment}")
                    
                    items = data.get('items', [])
                    if not items:
                        break
                    
                    segment_vacancies.extend(items)
                    
                    if page >= data.get('pages', 0) - 1:
                        break
                    
                    # Ограничение на глубину
                    if page >= 19:
                        print(f"   Достигнут лимит страниц")
                        break
                    
                    page += 1
                    time.sleep(REQUEST_DELAY)
                else:
                    break
            except Exception as e:
                print(f"   Ошибка: {e}")
                break
        
        # Добавляем уникальные вакансии
        new_count = 0
        for item in segment_vacancies:
            vacancy_id = item.get('id')
            if vacancy_id and vacancy_id not in unique_ids:
                unique_ids.add(vacancy_id)
                all_vacancies.append(item)
                new_count += 1
        
        print(f"   Добавлено уникальных: {new_count}")
        print(f"   Всего собрано: {len(all_vacancies)}")
    
    return all_vacancies


def parse_vacancy(item: Dict) -> Dict:
    """Парсит данные вакансии"""
    vacancy = {
        'id': item.get('id', ''),
        'name': item.get('name', ''),
        'company': item.get('employer', {}).get('name', ''),
        'company_url': item.get('employer', {}).get('alternate_url', ''),
        'salary': 'не указана',
        'experience': item.get('experience', {}).get('name', ''),
        'schedule': item.get('schedule', {}).get('name', ''),
        'employment': item.get('employment', {}).get('name', ''),
        'area': item.get('area', {}).get('name', ''),
        'published_at': item.get('published_at', ''),
        'url': item.get('alternate_url', ''),
        'requirement': item.get('snippet', {}).get('requirement', ''),
        'responsibility': item.get('snippet', {}).get('responsibility', ''),
        'premium': item.get('premium', False),
        'has_test': item.get('has_test', False)
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


def collect_all_vacancies() -> List[Dict]:
    """Собирает все вакансии по всем ключевым словам"""
    print("=" * 60)
    print("СБОР ВАКАНСИЙ СИСТЕМНЫХ АДМИНИСТРАТОРОВ В МОСКВЕ")
    print(f"Время: {datetime.now()}")
    print("Метод: адаптивный (с сегментацией при необходимости)")
    print("=" * 60)
    
    all_vacancies = []
    unique_ids = set()
    total_stats = {
        'total_found': 0,
        'total_collected': 0,
        'by_keyword': {}
    }
    
    for keyword in SEARCH_KEYWORDS:
        vacancies, stats = get_vacancies_with_pagination_fix(keyword, '1')
        
        total_stats['by_keyword'][keyword] = stats
        total_stats['total_found'] += stats['found']
        
        # Добавляем уникальные вакансии
        new_count = 0
        for item in vacancies:
            vacancy_id = item.get('id')
            if vacancy_id and vacancy_id not in unique_ids:
                unique_ids.add(vacancy_id)
                vacancy = parse_vacancy(item)
                all_vacancies.append(vacancy)
                new_count += 1
        
        print(f"📌 Добавлено уникальных: {new_count}")
        print(f"📊 Всего уникальных: {len(all_vacancies)}")
    
    total_stats['total_collected'] = len(all_vacancies)
    
    # Итоговая статистика
    print(f"\n{'='*60}")
    print("ИТОГОВАЯ СТАТИСТИКА")
    print(f"{'='*60}")
    
    for keyword, stats in total_stats['by_keyword'].items():
        completeness = (stats['collected'] / stats['found'] * 100) if stats['found'] > 0 else 0
        print(f"'{keyword}':")
        print(f"  - Найдено: {stats['found']}")
        print(f"  - Собрано: {stats['collected']} ({completeness:.1f}%)")
        print(f"  - Метод: {stats['method']}")
    
    print(f"\nВСЕГО уникальных вакансий: {total_stats['total_collected']}")
    
    # Сортировка по дате
    try:
        all_vacancies.sort(key=lambda x: x.get('published_at', ''), reverse=True)
    except:
        pass
    
    return all_vacancies


def save_vacancies(vacancies: List[Dict], filename: str = 'hh_vacancies.json'):
    """Сохраняет вакансии в JSON файл"""
    stats = {
        'total': len(vacancies),
        'with_salary': sum(1 for v in vacancies if v['salary'] != 'не указана'),
        'companies': len(set(v['company'] for v in vacancies if v['company'])),
        'premium': sum(1 for v in vacancies if v.get('premium', False)),
        'with_test': sum(1 for v in vacancies if v.get('has_test', False))
    }
    
    # Статистика по графикам
    schedules = {}
    for v in vacancies:
        schedule = v.get('schedule', 'Не указан')
        schedules[schedule] = schedules.get(schedule, 0) + 1
    
    output = {
        'source': 'hh.ru',
        'search_keywords': SEARCH_KEYWORDS,
        'search_params': {
            'area': 'Москва',
            'area_id': '1',
            'search_field': 'В названии вакансии',
            'method': 'Адаптивный с сегментацией'
        },
        'updated': datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ'),
        'statistics': stats,
        'schedule_distribution': schedules,
        'total_count': len(vacancies),
        'vacancies': vacancies
    }
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 Файл {filename} создан")
    print(f"📊 Сохранено {len(vacancies)} вакансий")


def main():
    """Основная функция"""
    try:
        vacancies = collect_all_vacancies()
        
        if vacancies:
            save_vacancies(vacancies)
            
            # Топ компаний
            companies = {}
            for v in vacancies:
                company = v['company']
                if company:
                    companies[company] = companies.get(company, 0) + 1
            
            top_companies = sorted(companies.items(), key=lambda x: x[1], reverse=True)[:5]
            print("\n🏢 Топ-5 компаний:")
            for company, count in top_companies:
                print(f"  - {company}: {count} вакансий")
        else:
            print("\n❌ Вакансии не найдены")
        
        print("\n✅ Готово!")
        
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
