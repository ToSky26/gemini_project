from parser.download_pdf import download_pdf
from parser.extract_images import parse_pdf
from parser.excel_export import create_excel
from parser.archiver import create_zip


def main():
    '''Запускает все этапы обработки варианта.'''
    pdf_path = download_pdf()

    tasks = parse_pdf(pdf_path)

    create_excel(tasks)

    create_zip()

    print('Обработка завершена!')


if __name__ == '__main__':
    main()
