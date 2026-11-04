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
    

def get_leaf_ids(df, id_column, parent_column):
    parent_ids = {
        to_int(value)
        for value in df[parent_column]
        if to_int(value) is not None
    }

    return {
        to_int(value)
        for value in df[id_column]
        if to_int(value) is not None
        and to_int(value) not in parent_ids
    }


def build_leaf_catalog(df, id_column, name_column, parent_column):
    rows = {}

    for _, row in df.iterrows():
        item_id = to_int(row[id_column])

        if item_id is not None:
            rows[item_id] = {
                'name': str(row[name_column]).strip(),
                'parent': to_int(row[parent_column]),
            }

    leaf_ids = get_leaf_ids(df, id_column, parent_column)
    catalog = []

    for leaf_id in sorted(leaf_ids):
        path = []
        current_id = leaf_id
        visited = set()

        while current_id in rows and current_id not in visited:
            visited.add(current_id)
            path.append(rows[current_id]['name'])
            current_id = rows[current_id]['parent']

        path.reverse()

        catalog.append({
            'id': leaf_id,
            'name': rows[leaf_id]['name'],
            'path': ' → '.join(path),
        })

    return catalog, leaf_ids


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

    exam_catalog, leaf_exam_ids = build_leaf_catalog(
        math_exams,
        'id',
        'name_of_Exam',
        'parent_of_exam',
    )

    topic_catalog, leaf_topic_ids = build_leaf_catalog(
        topics,
        'id',
        'name',
        'parent',
    )

    task_catalog = [
        {
            'task_num': task.get('task_num'),
            'condition': str(task.get('condition', '')),
        }
        for task in tasks
    ]

    valid_exam_ids = leaf_exam_ids
    valid_topic_ids = leaf_topic_ids

    def make_prompt(tasks_to_classify, correction_info=None):
        correction_text = ''

        if correction_info:
            correction_text = f'''
ПРЕДЫДУЩАЯ ПОПЫТКА СОДЕРЖАЛА ОШИБКИ.

Исправь классификацию следующих заданий.
Причины ошибок:
{json.dumps(correction_info, ensure_ascii=False)}

Не повторяй предыдущие ошибки.
Для каждого задания обязательно выбери оба ID.
'''

        return f'''
Ты — эксперт по классификации заданий ЕГЭ по профильной математике.

Для каждого задания выбери:
- exams_id — одну конечную категорию из каталога экзаменов;
- topics_id — одну конечную категорию из каталога тем.

ОСНОВНЫЕ ПРАВИЛА:

1. Внимательно изучи полное условие каждого задания.
2. Определи, какие математические знания и методы
   необходимы для решения.
3. Выбирай тему по математическому содержанию и методу
   решения, а не только по словам из условия.
4. Учитывай весь путь категории в каталоге:
   родительские разделы помогают определить контекст темы.
5. Выбирай наиболее подходящую конечную категорию.
6. Не выбирай общие, родительские или промежуточные категории.
7. Если точного соответствия нет, выбери наиболее близкую
   по математическому содержанию и методу решения конечную тему.
8. Не выбирай случайную тему только ради заполнения поля.
   Сначала сравни все подходящие конечные категории.
9. Используй исключительно ID из переданных каталогов.
10. Не придумывай ID.
11. Для каждого задания обязательно верни ровно один
    exams_id и ровно один topics_id.
12. Не возвращай null, пустые строки или пропущенные поля.
13. Сохраняй исходный task_num.
14. Не изменяй условия заданий.
15. Подпункты А), Б), В) одного задания рассматривай
    как одно задание и присваивай ему одну тему.

ПЕРЕД ВЫБОРОМ topics_id:
- Сравни условие задания с названиями конечных тем.
- Учитывай математический метод, необходимый для решения.
- Проверь, какая конечная тема наиболее точно описывает
  именно этот метод.
- Не ограничивайся первым подходящим совпадением.

{correction_text}

ФОРМАТ ОТВЕТА — СТРОГО JSON:

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
{json.dumps(tasks_to_classify, ensure_ascii=False)}
'''

    def request_classification(tasks_to_classify, correction_info=None):
        prompt = make_prompt(tasks_to_classify, correction_info)
        response = generate_with_fallback([prompt])

        result = parse_json_response(response_to_text(response))

        if not isinstance(result, dict) or not isinstance(
            result.get('tasks'), list
        ):
            raise ValueError('Gemini вернул JSON неправильной структуры')

        return result['tasks']

    def validate_response(tasks_to_classify, response_items):
        expected_nums = {
            normalize_task_num(task.get('task_num'))
            for task in tasks_to_classify
        }

        returned_by_num = {}
        duplicate_nums = set()

        for item in response_items:
            if not isinstance(item, dict):
                continue

            task_num = normalize_task_num(item.get('task_num'))

            if task_num not in expected_nums:
                continue

            if task_num in returned_by_num:
                duplicate_nums.add(task_num)
            else:
                returned_by_num[task_num] = item

        valid_results = {}
        errors = {}

        for task in tasks_to_classify:
            task_num = normalize_task_num(task.get('task_num'))

            if task_num in duplicate_nums:
                errors[task_num] = 'Gemini вернул задание несколько раз'
                continue

            item = returned_by_num.get(task_num)

            if item is None:
                errors[task_num] = 'Задание отсутствует в ответе Gemini'
                continue

            exam_id = to_int(item.get('exams_id'))
            topic_id = to_int(item.get('topics_id'))

            if exam_id not in valid_exam_ids:
                errors[task_num] = (
                    f'Некорректный или не конечный exams_id: {exam_id}'
                )
                continue

            if topic_id not in valid_topic_ids:
                errors[task_num] = (
                    f'Некорректный или не конечный topics_id: {topic_id}'
                )
                continue

            valid_results[task_num] = {
                'exams_id': exam_id,
                'topics_id': topic_id,
            }

        return valid_results, errors

    print(f'Отправляю Gemini {len(tasks)} заданий (попытка 1 из 2)...')

    try:
        first_response = request_classification(task_catalog)
        valid_results, errors = validate_response(
            task_catalog,
            first_response,
        )
    except Exception as error:
        print(f'Первая попытка классификации не удалась: {error}')

        valid_results = {}
        errors = {
            normalize_task_num(task.get('task_num')):
                'Не удалось обработать первый ответ Gemini'
            for task in tasks
        }

    if errors:
        retry_tasks = [
            task for task in task_catalog
            if normalize_task_num(task.get('task_num')) in errors
        ]

        print(
            f'Найдены ошибки в {len(retry_tasks)} заданиях. '
            f'Отправляю их на исправление (попытка 2 из 2)...'
        )

        try:
            second_response = request_classification(
                retry_tasks,
                errors,
            )

            second_valid, second_errors = validate_response(
                retry_tasks,
                second_response,
            )

            valid_results.update(second_valid)
            errors = second_errors

        except Exception as error:
            print(f'Вторая попытка классификации не удалась: {error}')

    for task in tasks:
        task_num = normalize_task_num(task.get('task_num'))
        result = valid_results.get(task_num)

        if result:
            task['exams_id'] = result['exams_id']
            task['topics_id'] = result['topics_id']
        else:
            task['exams_id'] = None
            task['topics_id'] = None

    if errors:
        error_details = '\n'.join(
            f'Задание {task_num}: {reason}'
            for task_num, reason in errors.items()
        )

        raise RuntimeError(
            'Не удалось классифицировать все задания '
            'за две попытки:\n' + error_details
        )

    print(
        f'Классификация завершена. '
        f'Получены оба ID для всех {len(tasks)} заданий.'
    )

    return tasks
