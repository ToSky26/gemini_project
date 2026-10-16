import os
from pathlib import Path

from dotenv import load_dotenv
from google import genai

PROJECT_DIR = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_DIR / '.env')
api_key = os.getenv('GEMINI_API_KEY')

if not api_key:
    raise ValueError('Не найден GEMINI_API_KEY. Проверь файл .env')

client = genai.Client(api_key=api_key)

response = client.models.generate_content(
    model='gemini-3.5-flash',
    contents='Реши уравнение 2x + 4 = 10. '
             'Покажи решение и ответ.'
)
print(response.text)
