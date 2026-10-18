import re


TASK_RE = re.compile(r'^[ \t]*(19|1[0-8]|[1-9])\s*\.[ \t]*')


def extract_tasks(document, images_by_page):
    tasks_by_number = {}
    for page_number, page in enumerate(document, start=1):
        middle_x = page.rect.width / 2

        columns = {'left': [], 'right': []}
        for block in page.get_text('blocks'):
            x0, y0, x1, y1, text = block[:5]
            if not text.strip():
                continue
            if y0 < 25 or y1 > page.rect.height - 25:
                continue
            if x1 <= middle_x:
                columns['left'].append((y0, text))
            elif x0 >= middle_x:
                columns['right'].append((y0, text))

        for column_blocks in columns.values():
            column_blocks.sort(key=lambda item: item[0])
            current_task_num = None
            current_lines = []

            for _, text in column_blocks:
                for line in text.splitlines():
                    line = line.strip()
                    match = TASK_RE.match(line)

                    if match:
                        if current_task_num is not None:
                            save_task(
                                tasks_by_number,
                                current_task_num,
                                current_lines,
                                page_number,
                                images_by_page
                            )

                        current_task_num = int(match.group(1))
                        current_lines = [line]

                    elif current_task_num is not None:
                        current_lines.append(line)

            if current_task_num is not None:
                save_task(
                    tasks_by_number,
                    current_task_num,
                    current_lines,
                    page_number,
                    images_by_page
                )

    tasks = [
        tasks_by_number[number]
        for number in sorted(tasks_by_number)
    ]

    if not tasks:
        raise ValueError('Задания не найдены.')

    print('Найдено заданий:', len(tasks))
    return tasks


def save_task(tasks_by_number, task_num, lines, page_number, images_by_page):
    condition = '\n'.join(lines).strip()
    image_name = next(
        (
            image['name']
            for image in images_by_page.get(page_number, [])
            if image.get('task_num') == task_num
        ),
        ''
    )
    task = {
        'task_num': task_num,
        'condition': condition,
        'image_name': image_name,
        'solution': '',
        'answer': '',
    }

    existing_task = tasks_by_number.get(task_num)
    if existing_task is None or len(condition) > len(
        existing_task['condition']
    ):
        tasks_by_number[task_num] = task
