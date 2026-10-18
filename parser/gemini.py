import json
import os
import re
import time

from dotenv import load_dotenv
from google import genai

from constants import (MODEL_NAME, CACHE_PATH, MAX_RETRIES,
                       MAX_QUOTA_WAIT_SECONDS, DEFAULT_RETRY_SECONDS)


class QuotaWaitTooLong(Exception):
    pass


load_dotenv()

api_key = os.getenv('GEMINI_API_KEY')
if not api_key:
    raise ValueError('Добавь GEMINI_API_KEY в файл .env')

client = genai.Client(api_key=api_key)
latex_cache = {}


def load_cache():
    global latex_cache

    if not CACHE_PATH.exists():
        latex_cache = {}
        return

    try:
        data = json.loads(CACHE_PATH.read_text(encoding='utf-8'))
        latex_cache = data if isinstance(data, dict) else {}
    except (json.JSONDecodeError, OSError) as error:
        print(f'Не удалось прочитать кэш: {error}')
        latex_cache = {}


def save_cache():
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    CACHE_PATH.write_text(
        json.dumps(latex_cache, ensure_ascii=False, indent=4),
        encoding='utf-8'
    )


def is_quota_error(error_text):
    return '429' in error_text or 'RESOURCE_EXHAUSTED' in error_text


def is_temporary_error(error_text):
    return any(
        marker in error_text.upper()
        for marker in ('503', 'UNAVAILABLE', '500', 'INTERNAL', '502', '504')
    )


def get_retry_delay(error_text):
    patterns = [
        r'retry in\s+(\d+(?:\.\d+)?)\s*s(?:ec(?:onds?)?)?',
        r'Please retry in\s+(\d+(?:\.\d+)?)\s*seconds?',
        r'retryDelay["\']?\s*:\s*["\']?(\d+(?:\.\d+)?)s',
    ]

    for pattern in patterns:
        match = re.search(pattern, error_text, re.IGNORECASE)
        if match:
            return max(1, float(match.group(1)))

    return DEFAULT_RETRY_SECONDS


def extract_json(response_text):
    response_text = (response_text or '').strip()
    response_text = re.sub(
        r'^```(?:json)?\s*',
        '',
        response_text,
        flags=re.IGNORECASE
    )
    response_text = re.sub(r'\s*```$', '', response_text)

    return json.loads(response_text)


def convert_condition_to_latex(condition, task_num):
    cache_key = f'{task_num}:{condition}'

    if cache_key in latex_cache:
        print(f'Задание {task_num}: использую кэш.')
        return latex_cache[cache_key]

    prompt = f"""
Преобразуй условие задания ЕГЭ по математике в LaTeX.

Номер задания: {task_num}

Исходное условие:
{condition}

Правила:
- Не решай задачу и не вычисляй ответ.
- Не добавляй объяснений.
- Не меняй числа и математический смысл.
- Сохрани русский текст и математические формулы.
- Не придумывай отсутствующие данные.
- Верни только JSON:
{{
    "condition_latex": "Условие в LaTeX"
}}
"""

    temporary_attempt = 0
    quota_attempt = 0

    while True:
        try:
            response = client.models.generate_content(
                model=MODEL_NAME,
                contents=prompt
            )

        except Exception as error:
            error_text = str(error)
            if is_quota_error(error_text):
                quota_attempt += 1
                wait_seconds = get_retry_delay(error_text)

                if wait_seconds > MAX_QUOTA_WAIT_SECONDS:
                    raise QuotaWaitTooLong(
                        f'Задание {task_num}: повтор через '
                        f'{wait_seconds:g} сек. '
                        'Запусти программу позже.'
                    ) from error

                if quota_attempt >= MAX_RETRIES:
                    raise QuotaWaitTooLong(
                        f'Задание {task_num}: квота не восстановилась '
                        f'после {quota_attempt} попыток.'
                    ) from error

                print(
                    f'Квота Gemini исчерпана. '
                    f'Повтор через {wait_seconds:g} сек.'
                )
                time.sleep(wait_seconds + 1)
                continue

            if is_temporary_error(error_text):
                temporary_attempt += 1

                if temporary_attempt < MAX_RETRIES:
                    wait_seconds = temporary_attempt * 5
                    print(
                        f'Временная ошибка. Повтор через {wait_seconds} сек.'
                    )
                    time.sleep(wait_seconds)
                    continue

                print(
                    f'Задание {task_num}: сервер недоступен. '
                    'Оставляю исходное условие.'
                )
                return condition

            raise

        try:
            data = extract_json(response.text)
        except (json.JSONDecodeError, TypeError) as error:
            print(f'Ошибка JSON в задании {task_num}: {error}')
            return condition

        if not isinstance(data, dict):
            print(f'Задание {task_num}: ожидался JSON-объект.')
            return condition

        condition_latex = data.get('condition_latex')

        if not isinstance(condition_latex, str) or not condition_latex.strip():
            print(f'Задание {task_num}: пустой или неверный результат.')
            return condition

        condition_latex = condition_latex.strip()
        latex_cache[cache_key] = condition_latex
        save_cache()

        print(f'Задание {task_num}: LaTeX сохранён в кэш.')
        return condition_latex


load_cache()
