#!/usr/bin/env python3
"""Скрипт для объединения файлов с вакансиями"""

import json
import os
import sys
from datetime import datetime


def merge_vacancy_files(input_dir='artifacts'):
    """Объединить все JSON файлы с вакансиями"""
    all_vacancies = {}
    total_count = 0
    files_processed = 0
    
    # Проходим по всем файлам в директории artifacts
    for root, dirs, files in os.walk(input_dir):
        for file in files:
            if file.endswith('.json') and file.startswith('vacancies_'):
                file_path = os.path.join(root, file)
                print(f"Processing: {file_path}")
                
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    # Извлекаем вакансии по регионам
                    vacancies_by_region = data.get('vacancies_by_region', {})
                    
                    for region_id, vacancies in vacancies_by_region.items():
                        if region_id not in all_vacancies:
                            all_vacancies[region_id] = []
                        
                        # Добавляем вакансии, избегая дубликатов
                        existing_ids = {v['id'] for v in all_vacancies[region_id]}
                        for vacancy in vacancies:
                            if vacancy['id'] not in existing_ids:
                                all_vacancies[region_id].append(vacancy)
                                total_count += 1
                    
                    files_processed += 1
                    
                except Exception as e:
                    print(f"Error processing {file_path}: {e}")
                    continue
    
    print(f"\nProcessed {files_processed} files")
    print(f"Total unique vacancies: {total_count}")
    print(f"Regions: {len(all_vacancies)}")
    
    # Сохранение объединенного результата
    result = {
        'merge_date': datetime.now().isoformat(),
        'total_vacancies': total_count,
        'regions_count': len(all_vacancies),
        'files_processed': files_processed,
        'vacancies_by_region': all_vacancies
    }
    
    with open('all_vacancies.json', 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    return result


def generate_summary(data):
    """Генерация summary в формате Markdown"""
    summary = f"""# Vacancy Parse Summary

**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M')}
**Total vacancies:** {data['total_vacancies']:,}
**Regions processed:** {data['regions_count']}
**Files merged:** {data.get('files_processed', 'N/A')}

## Top 10 regions by vacancy count:

| Region ID | Vacancies |
|-----------|-----------|
"""
    
    # Подсчет вакансий по регионам
    region_counts = [(region_id, len(vacancies)) 
                     for region_id, vacancies in data['vacancies_by_region'].items()]
    region_counts.sort(key=lambda x: x[1], reverse=True)
    
    for region_id, count in region_counts[:10]:
        summary += f"| {region_id} | {count:,} |\n"
    
    # Добавляем общую статистику
    if region_counts:
        avg_vacancies = sum(c[1] for c in region_counts) / len(region_counts)
        summary += f"\n**Average vacancies per region:** {avg_vacancies:.0f}"
    
    with open('summary.md', 'w', encoding='utf-8') as f:
        f.write(summary)
    
    print("\nSummary:")
    print(summary)
    
    return summary


if __name__ == "__main__":
    # Объединяем файлы
    result = merge_vacancy_files()
    
    # Генерируем summary
    if result['total_vacancies'] > 0:
        generate_summary(result)
    else:
        print("No vacancies found!")
        sys.exit(1)
