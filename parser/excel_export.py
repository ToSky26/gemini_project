import json
from datetime import date
import re

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font

from constants import (
    EXCEL_PATH,
    ANSWERS_PATH,
    SOURCE_URL,
    VARIANT_NAME,
    CLASS_NUMBER,
    YEAR,
)
from parser.latex_cleaner import clean_latex


def format_condition(condition):
    if not condition:
        return condition

    condition = re.sub(
        r'\s*([АБВГДЕЖЗ])\s*\)',
        r'<br>\1)',
        condition,
        flags=re.IGNORECASE
    )

    return condition.strip()


def load_answers():
    if not ANSWERS_PATH.exists():
        return {}

    try:
        with ANSWERS_PATH.open('r', encoding='utf-8') as file:
            return json.load(file)
    except (json.JSONDecodeError, OSError) as error:
        print(f'Не удалось прочитать answers.json: {error}')
        return {}


def create_excel(tasks):
    workbook = Workbook()

    tasks_sheet = workbook.active
    tasks_sheet.title = 'Tasks'

    headers = [
        'task_num',
        'condition',
        'image_name',
        'solution',
        'answer',
        'exams_id',
        'topics_id',
    ]
    tasks_sheet.append(headers)

    answers = load_answers()

    for task in tasks:
        task_num = task['task_num']

        answer = task.get('answer', '')
        if not answer:
            answer = answers.get(
                str(task_num),
                answers.get(task_num, ''),
            )

        condition = clean_latex(
            task.get('condition', ''),
            task_num,
        )
        condition = format_condition(condition)

        tasks_sheet.append([
            task_num,
            condition,
            task.get('image_name', ''),
            task.get('solution', ''),
            answer,
            task.get('exams_id') or '',
            task.get('topics_id') or '',
        ])

    about_sheet = workbook.create_sheet('about')

    metadata = [
        ['Класс', CLASS_NUMBER],
        ['Год', YEAR],
        ['Дата создания', date.today().isoformat()],
        ['topic', 1],
        ['exam_id', 1],
        ['Название варианта', VARIANT_NAME],
        ['source_name', 'Алекс Ларин'],
        ['is_public', 'True'],
        ['Ссылка на источник', SOURCE_URL],
    ]

    for row in zip(*metadata):
        about_sheet.append(list(row))

    header_font = Font(bold=True)
    body_alignment = Alignment(
        horizontal='left',
        vertical='top',
        wrap_text=True,
    )
    header_alignment = Alignment(
        horizontal='center',
        vertical='center',
        wrap_text=True,
    )

    for sheet in workbook.worksheets:
        for row in sheet.iter_rows():
            for cell in row:
                cell.alignment = body_alignment

        for cell in sheet[1]:
            cell.font = header_font
            cell.alignment = header_alignment

    tasks_sheet.column_dimensions['A'].width = 12
    tasks_sheet.column_dimensions['B'].width = 100
    tasks_sheet.column_dimensions['C'].width = 30
    tasks_sheet.column_dimensions['D'].width = 30
    tasks_sheet.column_dimensions['E'].width = 20
    tasks_sheet.column_dimensions['F'].width = 15
    tasks_sheet.column_dimensions['G'].width = 15
    tasks_sheet.row_dimensions[1].height = 30
    tasks_sheet.freeze_panes = 'A2'

    about_column_widths = {
        'A': 12,
        'B': 12,
        'C': 18,
        'D': 12,
        'E': 12,
        'F': 35,
        'G': 25,
        'H': 15,
        'I': 65,
    }

    for column, width in about_column_widths.items():
        about_sheet.column_dimensions[column].width = width

    EXCEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    workbook.save(EXCEL_PATH)

    print(f'Excel сохранён: {EXCEL_PATH}')
