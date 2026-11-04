from constants import PDF_PATH
from parser.download_pdf import download_pdf
from parser.pdf_parser import parse_pdf
from parser.extract_answers import extract_answers
from parser.excel_export import create_excel
from parser.archiver import create_zip
from parser.classify_tasks import classify_tasks


def main():
    print('Шаг 1. Скачиваю PDF...')

    pdf_path = download_pdf()

    if not pdf_path:
        pdf_path = PDF_PATH

    print('\nШаг 2. Извлекаю ответы...')

    try:
        extract_answers()
    except Exception as error:
        print(f'Не удалось получить ответы: {error}')
        print('Продолжаю обработку заданий.')

    print('\nШаг 3. Распознаю задания и чертежи...')

    tasks = parse_pdf(pdf_path)

    if not tasks:
        raise RuntimeError(
            'Не удалось извлечь ни одного задания из PDF.'
        )

    print('\nШаг 4. Определяю экзамены и темы...')

    try:
        tasks = classify_tasks(tasks)
    except Exception as error:
        print(f'Ошибка классификации: {error}')
        raise

    print('\nШаг 5. Создаю Excel...')

    create_excel(tasks)

    print('\nШаг 6. Создаю ZIP-архив...')

    create_zip()

    print('\nОбработка завершена!')


if __name__ == '__main__':
    main()
