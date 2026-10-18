from parser.download_pdf import download_pdf
from parser.pdf_parser import parse_pdf
from parser.extract_answers import extract_answers
from parser.excel_export import create_excel
from parser.archiver import create_zip
from parser.gemini import QuotaWaitTooLong


def main():
    try:
        pdf_path = download_pdf()
        tasks = parse_pdf(pdf_path)
        answers = extract_answers()
        for task in tasks:
            task['answer'] = answers.get(task['task_num'], '')
        create_excel(tasks)
        create_zip()
        print('Обработка завершена!')

    except QuotaWaitTooLong as error:
        print(f'\n{error}')
        print('Уже обработанные условия сохранены в кэше.')


if __name__ == '__main__':
    main()
