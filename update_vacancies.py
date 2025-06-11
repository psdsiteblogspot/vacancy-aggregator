import requests
import json
from datetime import datetime

# API HH.ru
url = "https://api.hh.ru/vacancies"

# Параметры поиска
params = {
    'text': 'системный администратор',
    'area': 113,  # Россия
    'per_page': 100,  # Максимум вакансий на страницу
    'page': 0
}

# Заголовки
headers = {
    'User-Agent': 'Mozilla/5.0'
}

# Собираем все вакансии
all_vacancies = []

# Получаем первую страницу
response = requests.get(url, params=params, headers=headers)
data = response.json()

# Сколько всего страниц
total_pages = data.get('pages', 1)
print(f"Найдено страниц: {total_pages}")

# Обрабатываем первую страницу
for item in data.get('items', []):
    vacancy = {
        'title': item.get('name', ''),
        'company': item.get('employer', {}).get('name', ''),
        'salary': 'не указана',
        'publishDate': item.get('published_at', '')[:10],  # Только дата
        'url': item.get('alternate_url', '')
    }
    
    # Обработка зарплаты
    if item.get('salary'):
        salary_data = item['salary']
        if salary_data.get('from') and salary_data.get('to'):
            vacancy['salary'] = f"от {salary_data['from']} до {salary_data['to']} {salary_data.get('currency', 'RUR')}"
        elif salary_data.get('from'):
            vacancy['salary'] = f"от {salary_data['from']} {salary_data.get('currency', 'RUR')}"
        elif salary_data.get('to'):
            vacancy['salary'] = f"до {salary_data['to']} {salary_data.get('currency', 'RUR')}"
    
    all_vacancies.append(vacancy)

# Получаем остальные страницы (максимум 5 страниц = 500 вакансий)
for page in range(1, min(total_pages, 5)):
    params['page'] = page
    response = requests.get(url, params=params, headers=headers)
    data = response.json()
    
    for item in data.get('items', []):
        vacancy = {
            'title': item.get('name', ''),
            'company': item.get('employer', {}).get('name', ''),
            'salary': 'не указана',
            'publishDate': item.get('published_at', '')[:10],
            'url': item.get('alternate_url', '')
        }
        
        if item.get('salary'):
            salary_data = item['salary']
            if salary_data.get('from') and salary_data.get('to'):
                vacancy['salary'] = f"от {salary_data['from']} до {salary_data['to']} {salary_data.get('currency', 'RUR')}"
            elif salary_data.get('from'):
                vacancy['salary'] = f"от {salary_data['from']} {salary_data.get('currency', 'RUR')}"
            elif salary_data.get('to'):
                vacancy['salary'] = f"до {salary_data['to']} {salary_data.get('currency', 'RUR')}"
        
        all_vacancies.append(vacancy)

print(f"Собрано вакансий: {len(all_vacancies)}")

# Формируем JSON
output = {
    'source': 'hh.ru',
    'updated': datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ'),
    'vacancies': all_vacancies
}

# Сохраняем в файл
with open('hh_vacancies.json', 'w', encoding='utf-8') as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

print("Файл hh_vacancies.json создан!")
