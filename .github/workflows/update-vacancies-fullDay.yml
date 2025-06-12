name: Update Vacancies Full Day

on:
  schedule:
    # Запуск 4 раза в день для разных групп регионов
    - cron: '0 0 * * *'    # 00:00 UTC
    - cron: '0 6 * * *'    # 06:00 UTC
    - cron: '0 12 * * *'   # 12:00 UTC
    - cron: '0 18 * * *'   # 18:00 UTC
  workflow_dispatch:
    inputs:
      regions:
        description: 'Region IDs (comma-separated)'
        required: false
        default: ''

jobs:
  parse-vacancies:
    runs-on: ubuntu-latest
    strategy:
      fail-fast: false
      matrix:
        region_group:
          - name: "major_cities"
            regions: "1,2,3,4,5,6,7,8,9,10"
          - name: "large_cities"
            regions: "11,12,13,14,15,16,17,18,19,20"
          - name: "medium_cities_1"
            regions: "21,22,23,24,25,26,27,28,29,30"
          - name: "medium_cities_2"
            regions: "31,32,33,34,35,36,37,38,39,40"
          - name: "medium_cities_3"
            regions: "41,42,43,44,45,46,47,48,49,50"
          - name: "small_cities_1"
            regions: "51,52,53,54,55,56,57,58,59,60"
          - name: "small_cities_2"
            regions: "61,62,63,64,65,66,67,68,69,70"
          - name: "small_cities_3"
            regions: "71,72,73,74,75,76,77,78,79,80"
          - name: "small_cities_4"
            regions: "81,82,83,84,85,86,87,88,89,90"
          - name: "small_cities_5"
            regions: "91,92,93,94,95,96,97,98,99,100,101,102,103,104,2019"
      max-parallel: 3
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.10'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install requests
    
    - name: Parse vacancies
      env:
        REGIONS: ${{ github.event.inputs.regions || matrix.region_group.regions }}
        OUTPUT_FILE: vacancies_${{ matrix.region_group.name }}.json
      run: |
        python update_vacancies_fullDay.py
    
    - name: Upload results
      uses: actions/upload-artifact@v4
      with:
        name: vacancies-${{ matrix.region_group.name }}
        path: vacancies_${{ matrix.region_group.name }}.json
        retention-days: 7

  merge-results:
    needs: parse-vacancies
    runs-on: ubuntu-latest
    if: success()
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.10'
    
    - name: Download all artifacts
      uses: actions/download-artifact@v4
      with:
        path: artifacts
    
    - name: Merge vacancy files
      run: |
        python -c "
import json
import os
from datetime import datetime

# Собираем все файлы
all_vacancies = {}
total = 0

for root, dirs, files in os.walk('artifacts'):
    for file in files:
        if file.endswith('.json'):
            with open(os.path.join(root, file), 'r') as f:
                data = json.load(f)
                for region, vacancies in data.get('vacancies_by_region', {}).items():
                    if region not in all_vacancies:
                        all_vacancies[region] = []
                    all_vacancies[region].extend(vacancies)
                    total += len(vacancies)

# Сохраняем объединенный файл
result = {
    'merge_date': datetime.now().isoformat(),
    'total_vacancies': total,
    'regions_count': len(all_vacancies),
    'vacancies_by_region': all_vacancies
}

with open('all_vacancies.json', 'w') as f:
    json.dump(result, f, ensure_ascii=False, indent=2)

print(f'Merged {total} vacancies from {len(all_vacancies)} regions')
        "
    
    - name: Generate summary
      run: |
        python -c "
import json
from datetime import datetime

with open('all_vacancies.json', 'r') as f:
    data = json.load(f)

summary = f'''# Vacancy Parse Summary

**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M')}
**Total vacancies:** {data['total_vacancies']:,}
**Regions processed:** {data['regions_count']}

## Top regions by vacancy count:
'''

# Подсчет вакансий по регионам
region_counts = [(r, len(v)) for r, v in data['vacancies_by_region'].items()]
region_counts.sort(key=lambda x: x[1], reverse=True)

for region, count in region_counts[:10]:
    summary += f'- Region {region}: {count:,} vacancies\\n'

with open('summary.md', 'w') as f:
    f.write(summary)

print(summary)
        "
    
    - name: Create release
      if: github.event_name == 'schedule' || github.event_name == 'workflow_dispatch'
      uses: softprops/action-gh-release@v1
      with:
        tag_name: vacancies-${{ github.run_number }}
        name: Vacancies Update ${{ github.run_number }}
        body_path: summary.md
        files: |
          all_vacancies.json
          summary.md
      env:
        GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
