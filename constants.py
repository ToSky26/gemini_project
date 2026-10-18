from pathlib import Path


VARIANT_NUMBER = 542
YEAR = 2026
CLASS_NUMBER = 11

SOURCE_URL = f'https://alexlarin.net/ege/{YEAR}/trvar{VARIANT_NUMBER}.html'
VARIANT_NAME = f'Тренировочный вариант № {VARIANT_NUMBER}'
IMAGE_URL = (
    f"https://alexlarin.net/ege/{YEAR}/"
    f"trvar{VARIANT_NUMBER}.png"
)


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / 'data'
PDF_DIR = DATA_DIR / 'raw'
IMAGES_DIR = BASE_DIR / 'images'


PDF_PATH = PDF_DIR / f'trvar{VARIANT_NUMBER}.pdf'
EXCEL_PATH = BASE_DIR / 'tasks.xlsx'
ZIP_PATH = BASE_DIR / 'result.zip'
CACHE_PATH = DATA_DIR / 'latex_cache.json'


MODEL_NAME = 'gemini-3.7-flash'
MAX_RETRIES = 3
MAX_QUOTA_WAIT_SECONDS = 300
DEFAULT_RETRY_SECONDS = 10
