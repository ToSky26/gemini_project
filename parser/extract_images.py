import re
import fitz

from constants import IMAGES_DIR


TASK_RE = re.compile(r'(?m)^[ \t]*(19|1[0-8]|[1-9])\.[ \t]+')


def extract_images(document):
    '''Извлекает изображения из PDF.'''
    IMAGES_DIR.mkdir(exist_ok=True)

    images_by_page = {}

    for page_number, page in enumerate(document, start=1):
        images_by_page[page_number] = []

        for image_number, image_info in enumerate(
            page.get_images(full=True),
            start=1
        ):
            xref = image_info[0]
            image_data = document.extract_image(xref)

            extension = image_data.get('ext', 'png')

            image_name = (
                f'page_{page_number:02d}_'
                f'img_{image_number:02d}.{extension}'
            )

            image_path = IMAGES_DIR / image_name
            image_path.write_bytes(image_data['image'])

            images_by_page[page_number].append(image_name)

            print('Сохранено изображение:', image_name)

    return images_by_page


def extract_tasks(document, images_by_page):
    full_text = ''
    page_ranges = []

    for page_number, page in enumerate(document, start=1):
        page_text = page.get_text('text')
        start = len(full_text)
        full_text += page_text + '\n'
        end = len(full_text)
        page_ranges.append((start, end, page_number))

    matches = list(TASK_RE.finditer(full_text))
    tasks_by_number = {}

    for index, match in enumerate(matches):
        task_num = int(match.group(1))
        start = match.start()

        if index + 1 < len(matches):
            end = matches[index + 1].start()
        else:
            end = len(full_text)

        condition = full_text[start:end].strip()
        condition = re.sub(r'[ \t]+', ' ', condition)
        condition = re.sub(r'\n{3,}', '\n\n', condition)
        page_number = 1

        for page_start, page_end, number in page_ranges:
            if page_start <= start < page_end:
                page_number = number
                break

        task = {
            'task_num': task_num,
            'condition': condition,
            'image_name': ', '.join(
                images_by_page.get(page_number, [])
            )
        }

        if (
            task_num not in tasks_by_number
            or len(condition)
            > len(tasks_by_number[task_num]['condition'])
        ):
            tasks_by_number[task_num] = task

    tasks = [
        tasks_by_number[number]
        for number in sorted(tasks_by_number)
    ]

    if not tasks:
        raise ValueError(
            'Задания не найдены. Проверь регулярное выражение TASK_RE.'
        )

    print('Найдено заданий:', len(tasks))
    return tasks


def parse_pdf(pdf_path):
    with fitz.open(pdf_path) as document:
        images_by_page = extract_images(document)
        tasks = extract_tasks(document, images_by_page)
    return tasks
