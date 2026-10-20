import json
import os
import re

import requests
from dotenv import load_dotenv
from google import genai
from google.genai import types
from playwright.sync_api import sync_playwright

from constants import SOURCE_URL, MODEL_NAME, IMAGE_URL, BASE_DIR
from parser.gemini import QuotaWaitTooLong

load_dotenv()


def save_answers(answers):
    answers_path = BASE_DIR / 'answers.json'
    answers_path.parent.mkdir(parents=True, exist_ok=True)

    saved_answers = {}

    if answers_path.exists():
        try:
            saved_answers = json.loads(
                answers_path.read_text(encoding='utf-8')
            )
        except (json.JSONDecodeError, OSError) as error:
            print(f'Не удалось прочитать сохранённые ответы: {error}')

    saved_answers.update({
        str(task_num): answer
        for task_num, answer in answers.items()
    })

    temp_path = answers_path.with_suffix('.tmp')
    temp_path.write_text(
        json.dumps(saved_answers, ensure_ascii=False, indent=4),
        encoding='utf-8',
    )
    temp_path.replace(answers_path)


def extract_image_answers():
    load_dotenv()

    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        raise ValueError('Добавь GEMINI_API_KEY в файл .env')

    response = requests.get(IMAGE_URL, timeout=30)
    response.raise_for_status()
    image_data = response.content

    mime_type = response.headers.get(
        'Content-Type', 'image/png'
    ).split(';')[0]

    client = genai.Client(api_key=api_key)

    prompt = """
Распознай ответы к заданиям ЕГЭ по математике на изображении.
Нужны задания 13, 14, 15, 16, 17, 18 и 19.

Правила:
- Не решай задания самостоятельно.
- Переписывай только ответы, видимые на изображении.
- Не угадывай неразборчивые ответы.
- Сохраняй математические выражения и обозначения.
- Верни только корректный JSON без Markdown и пояснений.

Формат:
{
    "13": "ответ",
    "14": "ответ",
    "15": "ответ",
    "16": "ответ",
    "17": "ответ",
    "18": "ответ",
    "19": "ответ"
}
"""

    try:
        result = client.models.generate_content(
            model=MODEL_NAME,
            contents=[
                prompt,
                types.Part.from_bytes(
                    data=image_data,
                    mime_type=mime_type,
                ),
            ],
        )
    except Exception as error:
        error_text = str(error)

        if (
            '429' in error_text
            or 'RESOURCE_EXHAUSTED' in error_text
        ):
            raise QuotaWaitTooLong(
                'Gemini ограничил запрос на распознавание ответов. '
                'Ответы, сохранённые ранее, остались в answers.json.'
            ) from error

        raise

    text = (result.text or '').strip()
    text = re.sub(
        r'^```(?:json)?\s*',
        '',
        text,
        flags=re.IGNORECASE,
    )
    text = re.sub(r'\s*```$', '', text)

    start = text.find('{')
    end = text.rfind('}')

    if start == -1 or end == -1:
        raise ValueError('Gemini не вернул JSON с ответами.')

    data = json.loads(text[start:end + 1])

    if not isinstance(data, dict):
        raise ValueError('Ответ Gemini должен быть JSON-объектом.')

    answers = {}

    for task_num in range(13, 20):
        value = data.get(str(task_num))

        if value is not None and str(value).strip():
            answers[task_num] = str(value).strip()

    missing = set(range(13, 20)) - set(answers)

    if missing:
        print(
            'Не распознаны ответы заданий:',
            sorted(missing),
        )

    return answers


def extract_answers():
    answers = {}

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page()

        try:
            page.goto(
                SOURCE_URL,
                wait_until='networkidle',
                timeout=60000,
            )

            page.locator('input[name="B2"]').click()
            page.wait_for_timeout(500)

            for task_num in range(1, 13):
                answer = page.locator(
                    f'input[name="T{task_num}"]'
                ).input_value().strip()

                if answer:
                    answers[task_num] = answer
        finally:
            browser.close()

    save_answers(answers)
    print(f'Получено ответов с сайта: {len(answers)}')
    print('Ответы сохранены в answers.json.')
    image_answers = extract_image_answers()
    answers.update(image_answers)
    save_answers(answers)
    print(f'Всего получено ответов за этот запуск: {len(answers)}')
    for task_num in sorted(answers):
        print(f'Задание {task_num}: {answers[task_num]}')

    return answers
