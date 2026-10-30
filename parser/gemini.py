import os
import time

from dotenv import load_dotenv
from google import genai
from google.genai import errors, types

from constants import MODEL_POOL, DEFAULT_RETRY_SECONDS


load_dotenv()

api_key = os.getenv('GEMINI_API_KEY')

if not api_key:
    raise ValueError('Добавь GEMINI_API_KEY в файл .env')

client = genai.Client(api_key=api_key)


class QuotaWaitTooLong(Exception):
    pass


def generate_with_fallback(contents):
    for model_name in MODEL_POOL:
        try:
            print(f'  Пробуем модель: {model_name}')

            response = client.models.generate_content(
                model=model_name,
                contents=contents,
                config=types.GenerateContentConfig(
                    response_mime_type='application/json'
                ),
            )

            print(f'  Ответ получен от {model_name}')
            return response

        except (errors.ServerError, errors.APIError) as error:
            print(f'  Модель {model_name} не сработала: {error}')
            time.sleep(DEFAULT_RETRY_SECONDS)

        except Exception as error:
            print(f'  Ошибка модели {model_name}: {error}')
            time.sleep(DEFAULT_RETRY_SECONDS)

    raise RuntimeError('Не удалось получить ответ ни от одной модели.')
