from pathlib import Path

import fitz

PROJECT_DIR = Path(__file__).resolve().parent.parent
PDF_PATH = PROJECT_DIR / 'data' / 'raw' / 'trvar542.pdf'
TEXT_PATH = PROJECT_DIR / 'data' / 'raw' / 'variant_542.txt'


def extract_text():
    if not PDF_PATH.exists():
        raise FileNotFoundError(
            f'PDF-файл не найден: {PDF_PATH}. '
            'Сначала запустите download_pdf.py'
        )

    with fitz.open(PDF_PATH) as document:
        print(f'Количество страниц: {len(document)}')
        pages_text = []
        for page_num, page in enumerate(document, start=1):
            page_text = page.get_text('text')
            pages_text.append(f'--- Страница {page_num} ---\n{page_text}')

            print(
                f'Страница {page_num}: '
                f'{len(page_text)} символов'
            )

        full_text = '\n\n'.join(pages_text)

    TEXT_PATH.parent.mkdir(parents=True, exist_ok=True)
    TEXT_PATH.write_text(full_text, encoding='utf-8')

    print(f'\nТекст сохранён: {TEXT_PATH}')
    print(f'Всего символов: {len(full_text)}')
    print('\nНачало извлечённого текста:')
    print(full_text[:1500])


if __name__ == '__main__':
    extract_text()
