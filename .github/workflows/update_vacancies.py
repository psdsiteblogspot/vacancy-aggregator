#!/usr/bin/env python3
# Упрощенная версия для тестирования

import json
from datetime import datetime

def main():
    print("🚀 Запуск обновления вакансий...")
    
    # Создаем тестовые данные
    test_vacancies = [
        {
            'title': 'Системный администратор Linux (удаленно)',
            'company': 'ООО ИТ-Решения',
            'salary': 'от 95 000 до 150 000 руб.',
            'publishDate': '2025-06-11',
            'url': 'https://hh.ru/search/vacancy?text=системный+администратор'
        },
        {
            'title': 'DevOps Engineer / Системный администратор',
            'company': 'Tech Innovation Ltd',
            'salary': 'от 120 000 до 200 000 руб.',
            'publishDate': '2025-06-11',
            'url': 'https://hh.ru/search/vacancy?text=системный+администратор'
        },
        {
            'title': 'Администратор Windows Server (remote)',
            'company': 'Digital Services Corp',
            'salary': 'от 80 000 до 130 000 руб.',
            'publishDate': '2025-06-11',
            'url': 'https://hh.ru/search/vacancy?text=системный+администратор'
        }
    ]
    
    # Создаем JSON структуру
    result = {
        'source': 'hh.ru',
        'updated': datetime.now().isoformat() + 'Z',
        'vacancies': test_vacancies
    }
    
    # Сохраняем в файл
    try:
        with open('hh_vacancies.json', 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        print(f"✅ Файл hh_vacancies.json создан с {len(test_vacancies)} тестовыми вакансиями")
        print(f"🕒 Время обновления: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
    except Exception as e:
        print(f"❌ Ошибка при сохранении файла: {e}")
        exit(1)

if __name__ == "__main__":
    main()
