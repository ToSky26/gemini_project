import json

from constants import BASE_DIR, EXCEL_PATH
from parser.download_pdf import download_pdf
from parser.pdf_parser import parse_pdf
from parser.extract_answers import extract_answers
from parser.excel_export import create_excel
from parser.archiver import create_zip
from parser.gemini import QuotaWaitTooLong


ANSWERS_PATH = BASE_DIR / 'answers.json'


def load_answers():
    if not ANSWERS_PATH.exists():
        return {}

    try:
        return json.loads(ANSWERS_PATH.read_text(encoding='utf-8'))
    except (json.JSONDecodeError, OSError) as error:
        print(f'Не удалось прочитать сохранённые ответы: {error}')
        return {}


def save_answers(answers):
    saved_answers = load_answers()

    saved_answers.update({
        str(task_num): answer
        for task_num, answer in answers.items()
    })

    ANSWERS_PATH.parent.mkdir(parents=True, exist_ok=True)

    temp_path = ANSWERS_PATH.with_suffix('.tmp')
    temp_path.write_text(
        json.dumps(saved_answers, ensure_ascii=False, indent=4),
        encoding='utf-8',
    )
    temp_path.replace(ANSWERS_PATH)


def main():
    try:
        print('Шаг 1. Получаю ответы...')
        answers = load_answers()

        if len(answers) >= 19:
            print('Использую ранее сохранённые ответы.')
        else:
            try:
                new_answers = extract_answers()
                save_answers(new_answers)
                answers.update(load_answers())
                print('Ответы сохранены.')
            except QuotaWaitTooLong as error:
                print(f'\n{error}')
                answers = load_answers()
                print('Продолжаю с ранее сохранёнными ответами.')

        print('Шаг 2. Загружаю PDF...')
        pdf_path = download_pdf()

        print('Шаг 3. Извлекаю задания и изображения...')
        tasks = parse_pdf(pdf_path)

        for task in tasks:
            task_num = task['task_num']
            task['answer'] = answers.get(
                str(task_num),
                answers.get(task_num, ''),
            )

        print('Шаг 4. Создаю Excel...')
        try:
            create_excel(tasks)
        except QuotaWaitTooLong as error:
            print(f'\n{error}')
            print('Excel сохранён с доступными результатами.')

        print('Шаг 5. Создаю ZIP-архив...')
        if EXCEL_PATH.exists():
            create_zip()
        else:
            print('Excel не создан, поэтому ZIP пропущен.')

        print('Обработка завершена!')

    except QuotaWaitTooLong as error:
        print(f'\n{error}')
        print('Уже обработанные условия сохранены в кэше.')
        print('Ответы сохранены в answers.json, если их удалось получить.')


if __name__ == '__main__':
    main()
