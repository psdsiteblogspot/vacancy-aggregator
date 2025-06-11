#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Агрегатор вакансий системного администратора с hh.ru
Получает только вакансии за последние 24 часа
"""

import requests
import json
import logging
from datetime import datetime, timedelta
import time
import sys
import os

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_vacancies():
    """
    Получает все актуальные вакансии системного администратора
    """
    url = "https://api.hh.ru/vacancies"
    headers = {
        'User-Agent': 'VacancyAggregator/1.0 (gradelift.ru)',
        'Accept': 'application/json'
    }
    
    params = {
        'text': 'системный администратор',
        'order_by': 'publication_time',
        'per_page': 100,
        'page': 0,
        'search_field': 'name'
    }
    
    logger.info("Поиск всех актуальных вакансий системного администратора")
    
    all_vacancies = []
    total_found = 0
    
    try:
        # Получаем первую страницу
        response = requests.get(url, params=params, headers=headers, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        total_found = data.get('found', 0)
        items = data.get('items', [])
        all_vacancies.extend(items)
        
        logger.info(f"Найдено {total_found} вакансий, загружено {len(items)} с первой страницы")
        
        # Получаем дополнительные страницы (максимум 5)
        pages = min(data.get('pages', 1), 5)
        
        for page in range(1, pages):
            params['page'] = page
            
            try:
                response = requests.get(url, params=params, headers=headers, timeout=30)
                response.raise_for_status()
                page_data = response.json()
                
                page_items = page_data.get('items', [])
                all_vacancies.extend(page_items)
                
                logger.info(f"Страница {page + 1}: загружено {len(page_items)} вакансий")
                
                # Пауза между запросами
                time.sleep(0.5)
                
            except requests.RequestException as e:
                logger.warning(f"Ошибка при загрузке страницы {page + 1}: {e}")
                continue
        
        logger.info(f"Всего загружено {len(all_vacancies)} вакансий")
        return all_vacancies, total_found
        
    except requests.RequestException as e:
        logger.error(f"Ошибка при запросе к API: {e}")
        return [], 0
    except Exception as e:
        logger.error(f"Неожиданная ошибка: {e}")
        return [], 0

def format_vacancy(vacancy):
    """
    Форматирует данные вакансии для JSON
    """
    # Обработка зарплаты
    salary_info = vacancy.get('salary')
    salary_text = "Не указана"
    
    if salary_info:
        salary_from = salary_info.get('from')
        salary_to = salary_info.get('to')
        currency = salary_info.get('currency', 'RUR')
        
        if salary_from and salary_to:
            salary_text = f"от {salary_from:,} до {salary_to:,} {currency}".replace(',', ' ')
        elif salary_from:
            salary_text = f"от {salary_from:,} {currency}".replace(',', ' ')
        elif salary_to:
            salary_text = f"до {salary_to:,} {currency}".replace(',', ' ')
    
    # Обработка даты публикации
    pub_date = vacancy.get('published_at', '')
    if pub_date:
        try:
            # Конвертируем ISO дату в простой формат
            dt = datetime.fromisoformat(pub_date.replace('Z', '+00:00'))
            pub_date_formatted = dt.strftime('%Y-%m-%d')
        except ValueError:
            pub_date_formatted = pub_date[:10]  # Берем только дату
    else:
        pub_date_formatted = datetime.now().strftime('%Y-%m-%d')
    
    # Получаем данные работодателя
    employer = vacancy.get('employer', {})
    company_name = employer.get('name', 'Не указано')
    
    return {
        "title": vacancy.get('name', 'Без названия'),
        "company": company_name,
        "salary": salary_text,
        "publishDate": pub_date_formatted,
        "url": vacancy.get('alternate_url', ''),
        "area": vacancy.get('area', {}).get('name', 'Не указано'),
        "experience": vacancy.get('experience', {}).get('name', 'Любой'),
        "employment": vacancy.get('employment', {}).get('name', 'Полная занятость')
    }

def create_json_output(vacancies_data, total_found):
    """
    Создает финальный JSON для сохранения
    """
    formatted_vacancies = []
    
    for vacancy in vacancies_data:
        try:
            formatted_vacancy = format_vacancy(vacancy)
            formatted_vacancies.append(formatted_vacancy)
        except Exception as e:
            logger.warning(f"Ошибка при форматировании вакансии: {e}")
            continue
    
    # Создаем итоговую структуру
    result = {
        "source": "hh.ru",
        "updated": datetime.now().isoformat() + "Z",
        "search_stats": {
            "search_text": "системный администратор",
            "total_found": total_found,
            "total_saved": len(formatted_vacancies),
            "update_interval": "каждые 3 часа"
        },
        "vacancies": formatted_vacancies
    }
    
    return result

def save_json(data, filename='hh_vacancies.json'):
    """
    Сохраняет данные в JSON файл
    """
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Данные успешно сохранены в {filename}")
        logger.info(f"Сохранено {len(data['vacancies'])} вакансий")
        return True
        
    except Exception as e:
        logger.error(f"Ошибка при сохранении файла {filename}: {e}")
        return False

def main():
    """
    Основная функция
    """
    logger.info("=" * 50)
    logger.info("Запуск агрегатора вакансий")
    logger.info("Поиск: системный администратор (все актуальные)")
    logger.info("=" * 50)
    
    try:
        # Получаем вакансии
        vacancies, total_found = get_vacancies()
        
        if not vacancies:
            logger.warning("Не удалось получить вакансии")
            return 1
        
        # Создаем JSON
        json_data = create_json_output(vacancies, total_found)
        
        # Сохраняем файл
        if save_json(json_data):
            logger.info("=" * 50)
            logger.info("УСПЕШНО ЗАВЕРШЕНО")
            logger.info(f"Найдено: {total_found} вакансий")
            logger.info(f"Сохранено: {len(json_data['vacancies'])} вакансий")
            logger.info(f"Файл: hh_vacancies.json")
            logger.info("=" * 50)
            return 0
        else:
            logger.error("Ошибка при сохранении данных")
            return 1
            
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")
        return 1

if __name__ == "__main__":
    exit(main())
