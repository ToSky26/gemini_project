import re
import requests

from urllib.parse import urljoin
from constants import SOURCE_URL, PDF_DIR, PDF_PATH


def create_folders():
    PDF_DIR.mkdir(parents=True, exist_ok=True)


def download_pdf():
    create_folders()
    print('Загружаю страницу варианта...')

    response = requests.get(SOURCE_URL, timeout=30)
    response.raise_for_status()

    pdf_links = re.findall(
        r'''href\s*=\s*["']([^"']+\.pdf(?:\?[^"']*)?)["']''',
        response.text, flags=re.IGNORECASE
    )

    if not pdf_links:
        raise ValueError('Ссылка на PDF не найдена.')

    pdf_url = urljoin(SOURCE_URL, pdf_links[0])
    print('Скачиваю PDF:', pdf_url)

    pdf_response = requests.get(pdf_url, timeout=60)
    pdf_response.raise_for_status()

    if not pdf_response.content.startswith(b'%PDF'):
        raise ValueError('Скачанный файл не является PDF.')

    PDF_PATH.write_bytes(pdf_response.content)
    print('PDF сохранён:', PDF_PATH)
    return PDF_PATH
