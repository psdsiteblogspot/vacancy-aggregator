import requests
import json
import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class HHVacancyParser:
    """Оптимизированный парсер вакансий с HH.ru"""
    
    def __init__(self):
        self.base_url = "https://api.hh.ru/vacancies"
        self.headers = {
            'User-Agent': 'VacancyAggregator/1.0 (your@email.com)'
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        
        # Основные регионы России (исключая ID 113)
        self.regions = [
            1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20,
            21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38,
            39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56,
            57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74,
            75, 76, 77, 78, 79, 80, 81, 82, 83, 84, 85, 86, 87, 88, 89, 90, 91, 92,
            93, 94, 95, 96, 97, 98, 99, 100, 101, 102, 103, 104, 2019
        ]
        
        # Лимиты API
        self.max_requests_per_region = 2000
        self.max_pages = 100  # HH.ru ограничивает до 100 страниц
        self.per_page = 20    # Максимум 100, но 20 оптимально для баланса
        
    def get_vacancies_for_region(self, region_id: int, date_from: Optional[str] = None) -> List[Dict]:
        """Получить вакансии для конкретного региона"""
        vacancies = []
        page = 0
        total_pages = 1
        requests_count = 0
        
        # Если не указана дата, берем вакансии за последние сутки
        if not date_from:
            date_from = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        
        params = {
            'area': region_id,
            'date_from': date_from,
            'per_page': self.per_page,
            'page': page
        }
        
        while page < total_pages and page < self.max_pages and requests_count < self.max_requests_per_region:
            try:
                response = self.session.get(self.base_url, params=params)
                requests_count += 1
                
                if response.status_code == 200:
                    data = response.json()
                    vacancies.extend(data.get('items', []))
                    
                    # Обновляем общее количество страниц
                    if page == 0:
                        total_pages = data.get('pages', 1)
                        logger.info(f"Регион {region_id}: найдено {data.get('found', 0)} вакансий на {total_pages} страницах")
                    
                    page += 1
                    params['page'] = page
                    
                    # Задержка между запросами для соблюдения rate limits
                    time.sleep(0.5)
                    
                elif response.status_code == 403:
                    logger.warning(f"Превышен лимит запросов для региона {region_id}")
                    break
                else:
                    logger.error(f"Ошибка {response.status_code} для региона {region_id}")
                    break
                    
            except Exception as e:
                logger.error(f"Ошибка при получении вакансий для региона {region_id}: {e}")
                break
        
        logger.info(f"Регион {region_id}: получено {len(vacancies)} вакансий за {requests_count} запросов")
        return vacancies
    
    def get_vacancy_details(self, vacancy_id: str) -> Optional[Dict]:
        """Получить детальную информацию о вакансии"""
        try:
            response = self.session.get(f"{self.base_url}/{vacancy_id}")
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Ошибка {response.status_code} при получении деталей вакансии {vacancy_id}")
                return None
        except Exception as e:
            logger.error(f"Ошибка при получении деталей вакансии {vacancy_id}: {e}")
            return None
    
    def parse_all_regions(self, date_from: Optional[str] = None) -> Dict[int, List[Dict]]:
        """Парсинг вакансий по всем регионам"""
        all_vacancies = {}
        
        for region_id in self.regions:
            logger.info(f"Начинаем парсинг региона {region_id}")
            vacancies = self.get_vacancies_for_region(region_id, date_from)
            if vacancies:
                all_vacancies[region_id] = vacancies
            
            # Большая задержка между регионами
            time.sleep(2)
        
        return all_vacancies
    
    def save_vacancies(self, vacancies: Dict[int, List[Dict]], filename: str = "vacancies.json"):
        """Сохранить вакансии в файл"""
        output_data = {
            'parse_date': datetime.now().isoformat(),
            'total_vacancies': sum(len(v) for v in vacancies.values()),
            'regions_count': len(vacancies),
            'vacancies_by_region': vacancies
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Сохранено {output_data['total_vacancies']} вакансий в файл {filename}")
    
    def get_vacancy_ids_with_details(self, vacancies: List[Dict], max_details: int = 100) -> List[Dict]:
        """Получить детальную информацию для списка вакансий"""
        detailed_vacancies = []
        
        for i, vacancy in enumerate(vacancies[:max_details]):
            if i > 0 and i % 10 == 0:
                logger.info(f"Получено деталей: {i}/{min(len(vacancies), max_details)}")
                time.sleep(1)  # Дополнительная задержка каждые 10 запросов
            
            details = self.get_vacancy_details(vacancy['id'])
            if details:
                detailed_vacancies.append(details)
            
            time.sleep(0.5)  # Задержка между запросами
        
        return detailed_vacancies


# Дополнительные стратегии для оптимизации

class OptimizedHHParser(HHVacancyParser):
    """Расширенный парсер с дополнительными оптимизациями"""
    
    def __init__(self):
        super().__init__()
        
        # Группировка регионов по федеральным округам для параллельной обработки
        self.federal_districts = {
            'central': [1, 32, 35, 38, 40, 41, 42, 44, 48, 50, 53, 54, 55, 62, 66, 2019],
            'northwest': [2, 49, 52, 58, 60, 68, 82, 87],
            'south': [10, 16, 45, 46, 51, 73, 93],
            'north_caucasus': [27, 57, 64, 76],
            'volga': [5, 6, 11, 18, 20, 22, 25, 36, 37, 61, 71, 79, 90],
            'ural': [3, 7, 43, 52],
            'siberian': [4, 12, 21, 23, 28, 30, 31, 65, 72, 85, 99],
            'far_east': [24, 26, 67, 84, 96, 97]
        }
    
    def get_vacancies_with_filters(self, region_id: int, filters: Dict) -> List[Dict]:
        """Получить вакансии с дополнительными фильтрами для уменьшения количества страниц"""
        vacancies = []
        
        # Базовые параметры
        base_params = {
            'area': region_id,
            'per_page': 50,  # Увеличиваем для меньшего количества запросов
            **filters
        }
        
        # Стратегия разбиения по зарплатам
        salary_ranges = [
            {'salary': None},  # Без указания зарплаты
            {'salary': 30000, 'only_with_salary': True},
            {'salary': 50000, 'only_with_salary': True},
            {'salary': 100000, 'only_with_salary': True},
            {'salary': 200000, 'only_with_salary': True}
        ]
        
        for salary_filter in salary_ranges:
            params = {**base_params, **salary_filter}
            page = 0
            
            while page < 40:  # Ограничиваем количество страниц для каждого диапазона
                params['page'] = page
                
                try:
                    response = self.session.get(self.base_url, params=params)
                    if response.status_code == 200:
                        data = response.json()
                        items = data.get('items', [])
                        if not items:
                            break
                        vacancies.extend(items)
                        page += 1
                        time.sleep(0.3)
                    else:
                        break
                except Exception as e:
                    logger.error(f"Ошибка при получении вакансий: {e}")
                    break
        
        # Удаляем дубликаты
        unique_vacancies = {v['id']: v for v in vacancies}
        return list(unique_vacancies.values())
    
    def parse_by_schedule(self) -> Dict[int, List[Dict]]:
        """Парсинг с учетом расписания для разных типов вакансий"""
        all_vacancies = {}
        
        # Разные стратегии для разных дней
        today = datetime.now().weekday()
        
        if today in [0, 2, 4]:  # Понедельник, среда, пятница - крупные города
            target_regions = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        elif today in [1, 3]:  # Вторник, четверг - средние города
            target_regions = self.regions[10:50]
        else:  # Выходные - остальные регионы
            target_regions = self.regions[50:]
        
        for region_id in target_regions:
            vacancies = self.get_vacancies_for_region(region_id)
            if vacancies:
                all_vacancies[region_id] = vacancies
            time.sleep(1.5)
        
        return all_vacancies


# Пример использования
if __name__ == "__main__":
    # Базовый парсер
    parser = HHVacancyParser()
    
    # Парсинг вакансий за последние сутки
    vacancies = parser.parse_all_regions()
    
    # Сохранение результатов
    parser.save_vacancies(vacancies, f"vacancies_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
    
    # Для получения деталей по некоторым вакансиям
    if vacancies and 1 in vacancies:  # Если есть вакансии из Москвы
        moscow_vacancies = vacancies[1][:10]  # Первые 10 вакансий
        detailed = parser.get_vacancy_ids_with_details(moscow_vacancies)
        
        with open("detailed_vacancies.json", "w", encoding="utf-8") as f:
            json.dump(detailed, f, ensure_ascii=False, indent=2)
