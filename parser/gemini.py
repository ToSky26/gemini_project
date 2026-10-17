import json
import os
import re

from dotenv import load_dotenv
from google import genai


load_dotenv()

api_key = os.getenv('GEMINI_API_KEY')

if not api_key:
    raise ValueError('Добавь GEMINI_API_KEY в файл .env')

client = genai.Client(api_key=api_key)


def convert_condition_to_latex(condition, task_num):
    '''Преобразует условие задания в LaTeX.'''

    prompt = f'''
Преобразуй условие задания ЕГЭ по математике в LaTeX.
Номер задания: {task_num}
Исходное условие:
{condition}
Правила:
- Не решай задачу.
- Не вычисляй ответ.
- Не добавляй объяснений.
- Не меняй числа и математический смысл.
- Сохрани русский текст и математические формулы.
- Не придумывай отсутствующие данные.
Верни только JSON:
{{
    "condition_latex": "Условие в LaTeX"
}}
'''

    response = client.models.generate_content(
        model='gemini-3.8-flash', contents=prompt
    )
    response_text = (response.text or '').strip()
    response_text = re.sub(r'^```(?:json)?\s*', '', response_text)
    response_text = re.sub(r'\s*```$', '', response_text)

    try:
        data = json.loads(response_text)
        return data.get('condition_latex', condition)

    except json.JSONDecodeError:
        print(f'Ошибка JSON в задании {task_num}')
        return condition
