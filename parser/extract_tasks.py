from pathlib import Path
import re

PROJECT_DIR = Path(__file__).resolve().parent.parent
TEXT_PATH = PROJECT_DIR / 'data' / 'raw' / 'variant_542.txt'
OUTPUT_PATH = PROJECT_DIR / 'data' / 'raw' / 'tasks_preview.txt'

TASK_PATTERN = re.compile(r'(?m)^[ \t]*(1[0-9]|[1-9])\.[ \t]+')


def extract_tasks():
    if not TEXT_PATH.exists():
        raise FileNotFoundError(
            f'Файл не найден: {TEXT_PATH}. '
            'Сначала запустите extract_text.py'
        )

    text = TEXT_PATH.read_text(encoding='utf-8')
    matches = list(TASK_PATTERN.finditer(text))
    if not matches:
        raise ValueError(
            'Заголовки заданий не найдены. '
            'Проверьте формат извлечённого текста.'
        )

    tasks = []
    for index, match in enumerate(matches):
        start = match.start()
        end = (
            matches[index + 1].start()
            if index + 1 < len(matches)
            else len(text)
        )

        task_num = int(match.group(1))
        condition = text[start:end].strip()
        tasks.append(
            f'{"=" * 30}\n'
            f'ЗАДАНИЕ {task_num}\n'
            f'{"=" * 30}\n'
            f'{condition}\n'
        )

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text('\n'.join(tasks), encoding='utf-8')
    found_numbers = [int(match.group(1)) for match in matches]

    print(f'Найдено заголовков: {len(matches)}')
    print(f'Номера заголовков: {found_numbers}')
    print(f'Результат сохранён: {OUTPUT_PATH}')


if __name__ == '__main__':
    extract_tasks()
