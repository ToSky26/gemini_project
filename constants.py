from pathlib import Path


SOURCE_URL = 'https://alexlarin.net/ege/2026/trvar542.html'

BASE_DIR = Path(__file__).resolve().parent

PDF_DIR = BASE_DIR / 'data' / 'raw'
IMAGES_DIR = BASE_DIR / 'images'

PDF_PATH = PDF_DIR / 'trvar542.pdf'
EXCEL_PATH = BASE_DIR / 'tasks.xlsx'
ZIP_PATH = BASE_DIR / 'result.zip'

VARIANT_NAME = 'Тренировочный вариант № 542'
CLASS_NUMBER = 11
YEAR = 2026
