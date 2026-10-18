import json
import re

import requests
from dotenv import load_dotenv
from google import genai
from google.genai import types
from playwright.sync_api import sync_playwright

from constants import SOURCE_URL, MODEL_NAME, IMAGE_URL

load_dotenv()


def extract_image_answers():
    response = requests.get(IMAGE_URL, timeout=30)
    response.raise_for_status()
    image_data = response.content

    client = genai.Client()

    prompt = """
    На изображении находятся ответы к заданиям ЕГЭ по математике.

    Распознай ответы на задания с номерами 13, 14, 15, 16, 17, 18 и 19.

    Правила:
    - Сохраняй математические выражения и обозначения.
    - Не решай задания самостоятельно.
    - Переписывай только ответы, которые действительно видны
      на изображении.
    - Если ответ неразборчив или отсутствует, не угадывай его.
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

    result = client.models.generate_content(
        model=MODEL_NAME,
        contents=[
            prompt,
            types.Part.from_bytes(
                data=image_data,
                mime_type="image/png",
            ),
        ],
    )

    text = (result.text or "").strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    data = json.loads(text)

    answers = {}
    for task_num in range(13, 20):
        value = data.get(str(task_num))
        if value is not None and str(value).strip():
            answers[task_num] = str(value).strip()

    missing = set(range(13, 20)) - answers.keys()
    if missing:
        raise ValueError(
            f"Gemini не распознал ответы заданий: {sorted(missing)}"
        )
    return answers


def extract_answers():
    answers = {}
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page()

        try:
            page.goto(SOURCE_URL, wait_until="networkidle", timeout=60000,)
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

    answers.update(extract_image_answers())
    print(f"\nПолучено ответов: {len(answers)}")
    for task_num in sorted(answers):
        print(f"Задание {task_num}: {answers[task_num]}")
    return answers
