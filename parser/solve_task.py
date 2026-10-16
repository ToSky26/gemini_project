import json
import os
from pathlib import Path

from dotenv import load_dotenv
from google import genai

import time
from google.genai.errors import ServerError

PROJECT_DIR = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_DIR / '.env')
api_key = os.getenv('GEMINI_API_KEY')

if not api_key:
    raise ValueError('Не найден GEMINI_API_KEY. Проверь файл .env')

client = genai.Client(api_key=api_key)


def solve_task(task_num, condition):
    prompt = f'''
Ты — эксперт по профильной математике ЕГЭ.

Реши задание номер {task_num}.

Условие:
{condition}

Требования:
1. Внимательно прочитай условие.
2. Если формула повреждена или условие неполное,
   не выдумывай недостающие данные.
3. Запиши решение пошагово.
4. Отдельно укажи итоговый ответ.
5. Сохраняй математические формулы в LaTeX.
6. Верни только корректный JSON с полями:
   task_num, condition, solution, answer.
7. Значения всех полей должны быть строками,
   кроме task_num, который должен быть числом.
'''

    for attempt in range(3):
        try:
            response = client.models.generate_content(
                model='gemini-flash-lite-latest',
                contents=prompt,
                config={
                    'response_mime_type': 'application/json',
                    'response_schema': {
                        'type': 'OBJECT',
                        'properties': {
                            'task_num': {'type': 'INTEGER'},
                            'condition': {'type': 'STRING'},
                            'solution': {'type': 'STRING'},
                            'answer': {'type': 'STRING'},
                        },
                        'required': [
                            'task_num',
                            'condition',
                            'solution',
                            'answer',
                        ],
                    },
                },
            )
            break

        except ServerError as error:
            if getattr(error, 'code', None) != 503 or attempt == 2:
                raise
            wait_seconds = 2 ** (attempt + 1)
            print(
                f'Gemini временно недоступна. '
                f'Повтор через {wait_seconds} сек.'
            )
            time.sleep(wait_seconds)

    result = json.loads(response.text)
    return result


if __name__ == '__main__':
    test_condition = (
        'Решите уравнение 2x + 4 = 10. '
        'В ответе укажите значение x.'
    )
    result = solve_task(1, test_condition)
    print(json.dumps(result, ensure_ascii=False, indent=2))
