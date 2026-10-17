from datetime import date

from openpyxl import Workbook
from openpyxl.styles import Alignment

from constants import EXCEL_PATH, SOURCE_URL, VARIANT_NAME, CLASS_NUMBER, YEAR
from parser.gemini import convert_condition_to_latex


def create_excel(tasks):
    '''Создаёт Excel-файл'''
    workbook = Workbook()
    tasks_sheet = workbook.active
    tasks_sheet.title = 'Tasks'

    tasks_sheet.append([
        'task_num', 'condition', 'image_name', 'solution', 'answer'
    ])

    for task in tasks:
        task_num = task['task_num']
        condition = task['condition']
        print(f'Преобразую задание {task_num} в LaTeX...')

        try:
            condition_latex = convert_condition_to_latex(condition, task_num)
        except Exception as error:
            print(f'Ошибка Gemini: {error}')
            condition_latex = condition

        tasks_sheet.append([
            task_num, condition_latex, task['image_name'], '', ''
        ])

    about_sheet = workbook.create_sheet('about')
    about_sheet.append(['field', 'value'])
    about_sheet.append(['class', CLASS_NUMBER])
    about_sheet.append(['year', YEAR])
    about_sheet.append(['date', date.today().isoformat()])
    about_sheet.append(['variant_name', VARIANT_NAME])
    about_sheet.append(['source_url', SOURCE_URL])

    for sheet in workbook.worksheets:
        sheet.freeze_panes = 'A2'
        sheet.auto_filter.ref = sheet.dimensions

        for row in sheet.iter_rows():
            for cell in row:
                cell.alignment = Alignment(vertical='top', wrap_text=True)

        for column_cells in sheet.columns:
            column_letter = column_cells[0].column_letter

            max_length = max(
                len(str(cell.value or ''))
                for cell in column_cells
            )

            sheet.column_dimensions[column_letter].width = min(max_length + 2, 60)

    workbook.save(EXCEL_PATH)
    print('Excel сохранён:', EXCEL_PATH)
