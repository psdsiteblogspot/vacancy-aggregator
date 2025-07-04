import requests
import json
import time
from datetime import datetime

# API HH.ru
BASE_URL = "https://api.hh.ru/vacancies"

# Заголовки для запросов
HEADERS = {
    'User-Agent': 'DiagnosticTool/1.0 (diagnostic@example.com)'
}


def precise_page_limit_test():
    """Точный тест ограничения страниц API HH.ru"""
    print("=" * 70)
    print("ТОЧНАЯ ДИАГНОСТИКА ОГРАНИЧЕНИЙ ПАГИНАЦИИ HH.RU API")
    print(f"Время: {datetime.now()}")
    print("=" * 70)
    
    # Базовые параметры - точно как в вашем парсере
    params = {
        'text': 'системный администратор',
        'area': '1',  # Москва
        'search_field': 'name',
        'per_page': 50,  # Как на сайте
        'page': 0
    }
    
    # Первый запрос
    print("\n1. АНАЛИЗ ПЕРВОГО ЗАПРОСА")
    print("-" * 70)
    
    try:
        response = requests.get(BASE_URL, params=params, headers=HEADERS, timeout=30)
        if response.status_code == 200:
            data = response.json()
            
            found = data.get('found', 0)
            pages = data.get('pages', 0)
            per_page = data.get('per_page', 0)
            items_count = len(data.get('items', []))
            
            print(f"✅ Найдено вакансий: {found}")
            print(f"📄 Количество страниц по API: {pages}")
            print(f"📏 Элементов на страницу: {per_page}")
            print(f"📦 Фактически на первой странице: {items_count}")
            print(f"🔢 Теоретически доступно: {pages * per_page}")
            
            # Проверяем альтернативный URL
            alt_url = data.get('alternate_url', '')
            print(f"🔗 Альтернативный URL: {alt_url}")
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return
    
    # Тест доступности страниц
    print("\n2. ТЕСТ ДОСТУПНОСТИ СТРАНИЦ")
    print("-" * 70)
    
    # Критические точки для проверки
    test_pages = [0, 9, 10, 19, 20, 25, 26, 27, 30]
    actual_pages_with_data = 0
    last_page_with_data = -1
    total_items = 0
    
    for page in test_pages:
        params['page'] = page
        
        try:
            response = requests.get(BASE_URL, params=params, headers=HEADERS, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                items = data.get('items', [])
                items_count = len(items)
                total_items += items_count
                
                if items_count > 0:
                    actual_pages_with_data += 1
                    last_page_with_data = page
                    print(f"✅ Страница {page:2d}: {items_count:2d} вакансий")
                else:
                    print(f"⚠️ Страница {page:2d}: ПУСТАЯ")
            else:
                print(f"❌ Страница {page:2d}: HTTP {response.status_code}")
                
        except Exception as e:
            print(f"❌ Страница {page:2d}: Ошибка {str(e)[:50]}")
        
        time.sleep(0.3)
    
    print(f"\n📊 Последняя страница с данными: {last_page_with_data}")
    print(f"📊 Всего страниц с данными: {actual_pages_with_data}")
    
    # Проверяем offset
    print("\n3. АНАЛИЗ OFFSET (page × per_page)")
    print("-" * 70)
    
    critical_offsets = [
        (9, 450),    # page 9, offset 450
        (10, 500),   # page 10, offset 500
        (19, 950),   # page 19, offset 950
        (20, 1000),  # page 20, offset 1000 - критическая точка!
        (21, 1050),  # page 21, offset 1050
    ]
    
    for page, offset in critical_offsets:
        params['page'] = page
        status = "?"
        
        try:
            response = requests.get(BASE_URL, params=params, headers=HEADERS, timeout=30)
            if response.status_code == 200:
                data = response.json()
                items = len(data.get('items', []))
                if items > 0:
                    status = f"✅ {items} вакансий"
                else:
                    status = "⚠️ ПУСТАЯ"
            else:
                status = f"❌ HTTP {response.status_code}"
        except:
            status = "❌ Ошибка"
        
        print(f"Offset {offset:4d} (page {page:2d}): {status}")
        time.sleep(0.3)
    
    # Финальный анализ
    print("\n4. АНАЛИЗ РЕЗУЛЬТАТОВ")
    print("-" * 70)
    
    # Рассчитываем максимально доступное количество
    if last_page_with_data >= 19:
        max_accessible = 1000  # offset limit
        print(f"🚫 ОБНАРУЖЕН ЛИМИТ: offset ≤ 1000")
        print(f"   При per_page=50 это максимум 20 страниц (0-19)")
        print(f"   Максимум доступно: {max_accessible} вакансий")
    else:
        max_accessible = (last_page_with_data + 1) * 50
        print(f"🚫 ОБНАРУЖЕН ЛИМИТ: максимум {last_page_with_data + 1} страниц")
        print(f"   Максимум доступно: {max_accessible} вакансий")
    
    print(f"\n📊 ИТОГО:")
    print(f"   Найдено по API: {found}")
    print(f"   Максимум доступно: {max_accessible}")
    print(f"   Потеряно: {found - max_accessible}")
    print(f"   Процент потерь: {((found - max_accessible) / found * 100):.1f}%")
    
    # Рекомендации
    print("\n5. РЕКОМЕНДАЦИИ ДЛЯ ПОЛУЧЕНИЯ ВСЕХ ВАКАНСИЙ")
    print("-" * 70)
    
    if found > 1000:
        print("✅ Используйте сегментацию по датам публикации:")
        print("   - За последние 1-3 дня")
        print("   - За последние 4-7 дней")
        print("   - За последние 8-14 дней")
        print("   - За последние 15-30 дней")
        print("\n✅ Или используйте дополнительные фильтры:")
        print("   - По опыту работы (experience)")
        print("   - По типу занятости (employment)")
        print("   - По графику работы (schedule)")
        print("\n✅ Или используйте более специфичные поисковые запросы:")
        print("   - 'системный администратор linux'")
        print("   - 'системный администратор windows'")
        print("   - 'сисадмин junior'")
        print("   - 'сисадмин middle'")


def test_date_segmentation():
    """Тест сегментации по датам"""
    print("\n\n" + "=" * 70)
    print("ТЕСТ СЕГМЕНТАЦИИ ПО ДАТАМ")
    print("=" * 70)
    
    from datetime import datetime, timedelta
    
    segments = [
        (1, "За последние 24 часа"),
        (3, "За последние 3 дня"),
        (7, "За последнюю неделю"),
        (30, "За последний месяц")
    ]
    
    total_found = 0
    
    for days, name in segments:
        date_from = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        date_to = datetime.now().strftime('%Y-%m-%d')
        
        params = {
            'text': 'системный администратор',
            'area': '1',
            'search_field': 'name',
            'date_from': date_from,
            'date_to': date_to,
            'per_page': 50,
            'page': 0
        }
        
        try:
            response = requests.get(BASE_URL, params=params, headers=HEADERS, timeout=30)
            if response.status_code == 200:
                data = response.json()
                found = data.get('found', 0)
                pages = data.get('pages', 0)
                total_found += found
                
                print(f"\n{name} ({date_from} - {date_to}):")
                print(f"  Найдено: {found} вакансий")
                print(f"  Страниц: {pages}")
                
                if pages > 20:
                    print(f"  ⚠️ Требуется дополнительная сегментация!")
                else:
                    print(f"  ✅ Можно получить все вакансии")
                    
        except Exception as e:
            print(f"❌ Ошибка: {e}")
        
        time.sleep(0.5)
    
    print(f"\n📊 Всего найдено через сегментацию: ~{total_found}")
    print("   (с учетом возможных дубликатов)")


def main():
    """Основная функция"""
    try:
        # Точный тест лимитов
        precise_page_limit_test()
        
        # Тест сегментации
        test_date_segmentation()
        
        print("\n✅ Диагностика завершена!")
        
    except KeyboardInterrupt:
        print("\n\n⚠️ Диагностика прервана")
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")


if __name__ == "__main__":
    main()
