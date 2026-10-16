from pathlib import Path

import fitz
import requests

PDF_URL = 'https://alexlarin.net/ege/2026/trvar542.pdf'
PROJECT_DIR = Path(__file__).resolve().parent.parent
PDF_PATH = PROJECT_DIR / 'data' / 'raw' / 'trvar542.pdf'


def download_pdf():
    PDF_PATH.parent.mkdir(parents=True, exist_ok=True)

    print('Начинаем скачивание PDF...')
    response = requests.get(PDF_URL, timeout=30)
    response.raise_for_status()
    if not response.content.startswith(b'%PDF-'):
        raise ValueError('Скачанный файл не PDF')

    PDF_PATH.write_bytes(response.content)
    print(f'Файл сохранён: {PDF_PATH}')
    print(f'Размер файла: {PDF_PATH.stat().st_size} байт')

    with fitz.open(PDF_PATH) as document:
        print(f'Количество страниц: {len(document)}')

        if len(document) == 0:
            raise ValueError('PDF не содержит страниц')
        print('PDF успешно открыт через PyMuPDF')


if __name__ == '__main__':
    download_pdf()
