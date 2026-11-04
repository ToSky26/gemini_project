from pathlib import Path

VARIANT_NUMBER = 541
YEAR = 2026
CLASS_NUMBER = 11
MATH_PROFILE_ID = 2

SOURCE_URL = f'https://alexlarin.net/ege/{YEAR}/trvar{VARIANT_NUMBER}.html'
VARIANT_NAME = f'Тренировочный вариант № {VARIANT_NUMBER}'

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / 'data'
PDF_DIR = DATA_DIR / 'raw'
IMAGES_DIR = BASE_DIR / 'images'

PDF_PATH = PDF_DIR / f'trvar{VARIANT_NUMBER}.pdf'
EXCEL_PATH = BASE_DIR / 'tasks.xlsx'
ZIP_PATH = BASE_DIR / 'result.zip'
ANSWERS_PATH = BASE_DIR / 'answers.json'
CACHE_PATH = DATA_DIR / 'latex_cache.json'

MODEL_POOL = [
    'gemini-3.8-flash',
    'gemini-3.7-flash',
    'gemini-3.5-flash-lite',
    'gemini-3.1-pro-preview',
    'gemini-3.1-flash-lite',
]
MODEL_NAME = 'gemini-3.5-flash-lite'
IMAGE_URL = (
    f'https://alexlarin.net/ege/{YEAR}/'
    f'trvar{VARIANT_NUMBER}.png'
)
MAX_RETRIES = 3
DEFAULT_RETRY_SECONDS = 2
