import re
import json
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font


PROJECT_DIR = Path(__file__).resolve().parent.parent
INPUT_PATH = PROJECT_DIR / 'data' / 'raw' / 'solved_tasks.json'
OUTPUT_PATH = PROJECT_DIR / 'tasks.xlsx'


def clean_excel_text(value):
    if not isinstance(value, str):
        return value
    value = value.replace('\x0crac{', r'\frac{')
    value = re.sub(r'[\x00-\x1F\x7F]', ' ', value,)
    value = re.sub(r' {2,}', ' ', value)
    return value


def main():
    with open(INPUT_PATH, 'r', encoding='utf-8') as file:
        tasks = json.load(file)
    for task in tasks:
        print(f'\nЗадание {task["task_num"]}:')
        print(repr(task.get('solution', '')[:500]))
    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = 'Задания'

    headers = ['Номер задания', 'Условие', 'Изображение', 'Решение', 'Ответ',]
    worksheet.append(headers)

    for task in tasks:
        worksheet.append([
            task['task_num'],
            clean_excel_text(task['condition']),
            clean_excel_text(task.get('image_name', '')),
            clean_excel_text(task['solution']),
            clean_excel_text(task['answer']),
        ])

    column_widths = {'A': 12, 'B': 60, 'C': 25, 'D': 90, 'E': 20}

    for column, width in column_widths.items():
        worksheet.column_dimensions[column].width = width

    for cell in worksheet[1]:
        cell.font = Font(bold=True)
        cell.alignment = Alignment(vertical='top', wrap_text=True,)

    for row in worksheet.iter_rows(min_row=2):
        for cell in row:
            cell.alignment = Alignment(vertical='top', wrap_text=True,)

    about = workbook.create_sheet('Информация')
    about.append(['Параметр', 'Значение'])
    about.append(['Класс', 11])
    about.append(['Год', 2026])
    about.append(['Номер варианта', 'Тренировочный вариант № 542'])
    about.append([
        'Ссылка', 'https://alexlarin.net/ege/2026/trvar542.html',
    ])

    about.column_dimensions['A'].width = 20
    about.column_dimensions['B'].width = 65

    for cell in about[1]:
        cell.font = Font(bold=True)

    for row in about.iter_rows():
        for cell in row:
            cell.alignment = Alignment(vertical='top', wrap_text=True,)

    workbook.save(OUTPUT_PATH)
    print(f'Excel-файл создан: {OUTPUT_PATH}')
    print(f'Количество заданий: {len(tasks)}')


if __name__ == '__main__':
    main()
