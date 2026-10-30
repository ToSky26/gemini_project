import json
import re
from pathlib import Path

import pandas as pd

from constants import DATA_DIR, MATH_PROFILE_ID
from parser.gemini import generate_with_fallback


EXAMS_PATH = Path(DATA_DIR) / 'exams.csv'
TOPICS_PATH = Path(DATA_DIR) / 'topics.csv'


def to_int(value):
    try:
        if pd.isna(value) or str(value).strip() == '':
            return None
        return int(float(value))
    except (TypeError, ValueError):
        return None


def normalize_task_num(value):
    if value is None:
        return ''

    try:
        return str(int(float(value)))
    except (TypeError, ValueError):
        return str(value).strip()


def load_catalogs():
    if not EXAMS_PATH.exists():
        raise FileNotFoundError(f'Не найден справочник: {EXAMS_PATH}')

    if not TOPICS_PATH.exists():
        raise FileNotFoundError(f'Не найден справочник: {TOPICS_PATH}')

    exams = pd.read_csv(EXAMS_PATH).fillna('')
    topics = pd.read_csv(TOPICS_PATH).fillna('')

    required_exam_columns = {
        'id',
        'name_of_Exam',
        'parent_of_exam',
    }
    required_topic_columns = {'id', 'name', 'parent', }

    if not required_exam_columns.issubset(exams.columns):
        raise ValueError('В exams.csv отсутствуют необходимые столбцы')

    if not required_topic_columns.issubset(topics.columns):
        raise ValueError('В topics.csv отсутствуют необходимые столбцы')
    exam_parents = {
        to_int(row['id']): to_int(row['parent_of_exam'])
        for _, row in exams.iterrows()
    }

    math_exam_ids = {MATH_PROFILE_ID}

    changed = True
    while changed:
        changed = False

        for exam_id, parent_id in exam_parents.items():
            if (
                exam_id is not None
                and parent_id in math_exam_ids
                and exam_id not in math_exam_ids
            ):
                math_exam_ids.add(exam_id)
                changed = True

    math_exams = exams[
        exams['id'].apply(to_int).isin(math_exam_ids)
    ].copy()

    return exams, topics, math_exams


def response_to_text(response):
    if isinstance(response, str):
        return response

    text = getattr(response, 'text', None)

    if text:
        return text

    raise ValueError('Gemini вернул ответ без текста')


def parse_json_response(text):
    text = text.strip()

    text = re.sub(r'^```(?:json)?\s*', '', text)
    text = re.sub(r'\s*```$', '', text)

    start = text.find('{')
    end = text.rfind('}')

    if start == -1 or end == -1:
        raise ValueError('В ответе Gemini не найден JSON')

    return json.loads(text[start:end + 1])


def classify_tasks(tasks):
    if not tasks:
        return tasks

    print('Загружаю справочники экзаменов и тем...')

    exams, topics, math_exams = load_catalogs()

    exam_catalog = [
        {
            'id': to_int(row['id']),
            'name': str(row['name_of_Exam']),
        }
        for _, row in math_exams.iterrows()
        if to_int(row['id']) is not None
    ]

    topic_catalog = [
        {
            'id': to_int(row['id']),
            'name': str(row['name']),
            'parent': to_int(row['parent']),
        }
        for _, row in topics.iterrows()
        if to_int(row['id']) is not None
    ]

    task_catalog = [
        {
            'task_num': task.get('task_num'),
            'condition': str(task.get('condition', '')),
        }
        for task in tasks
    ]

    prompt = f'''
Ты классифицируешь задания варианта ЕГЭ по профильной математике.

Для каждого задания выбери:
- exams_id — один подходящий ID из каталога экзаменов;
- topics_id — один подходящий ID из каталога тем.

Правила:
1. Используй исключительно ID из переданных каталогов.
2. Не придумывай ID.
3. Для каждого задания обязательно постарайся подобрать наиболее подходящую тему.
4. Если задание содержит несколько математических разделов,
   выбирай тему, которая отражает основной метод решения.
5. Не выбирай слишком общую тему, если есть более точная.
6. Если точного совпадения нет, выбирай ближайшую по смыслу тему.
7. Не возвращай null только из-за сложности условия.
8. Сохраняй исходный task_num.
9. Не изменяй условия заданий.

Формат ответа:
{{
    "tasks": [
        {{
            "task_num": 1,
            "exams_id": 7,
            "topics_id": 123
        }}
    ]
}}

КАТАЛОГ ЭКЗАМЕНОВ:
{json.dumps(exam_catalog, ensure_ascii=False)}

КАТАЛОГ ТЕМ:
{json.dumps(topic_catalog, ensure_ascii=False)}

ЗАДАНИЯ:
{json.dumps(task_catalog, ensure_ascii=False)}
'''

    print(f'Отправляю Gemini {len(tasks)} заданий...')

    response = generate_with_fallback([prompt])
    result = parse_json_response(response_to_text(response))

    if not isinstance(result, dict) or not isinstance(
        result.get('tasks'), list
    ):
        raise ValueError('Gemini вернул JSON неправильной структуры')

    returned_by_num = {}

    for item in result['tasks']:
        if not isinstance(item, dict):
            continue

        task_num = normalize_task_num(item.get('task_num'))

        if not task_num:
            continue

        if task_num in returned_by_num:
            returned_by_num[task_num] = None
        else:
            returned_by_num[task_num] = item

    valid_exam_ids = {
        to_int(value)
        for value in math_exams['id']
        if to_int(value) is not None
    }

    valid_topic_ids = {
        to_int(value)
        for value in topics['id']
        if to_int(value) is not None
    }

    matched = 0

    for task in tasks:
        task_num = normalize_task_num(task.get('task_num'))
        item = returned_by_num.get(task_num)

        if not isinstance(item, dict):
            task['exams_id'] = None
            task['topics_id'] = None
            continue

        exam_id = to_int(item.get('exams_id'))
        topic_id = to_int(item.get('topics_id'))

        task['exams_id'] = (
            exam_id if exam_id in valid_exam_ids else None
        )

        task['topics_id'] = (
            topic_id if topic_id in valid_topic_ids else None
        )

        if task['exams_id'] is not None or task['topics_id'] is not None:
            matched += 1

    print(
        f'Классификация завершена. '
        f'Получены ID для {matched} '
        f'из {len(tasks)} заданий.'
    )

    return tasks
