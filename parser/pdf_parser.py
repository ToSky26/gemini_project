import io
import json
import shutil

import pymupdf
from PIL import Image

from constants import PDF_PATH, IMAGES_DIR
from parser.gemini import generate_with_fallback


PROMPT = '''
Проанализируй изображение страницы математического варианта ЕГЭ.

1. Извлеки все задания на странице.
Для каждого задания укажи:
- task_number — номер задания;
- condition — полное условие без номера задания.

Сохрани русский текст, числа и математический смысл.
Формулы записывай в LaTeX, используя $...$ или $$...$$.

2. Найди геометрические чертежи и схемы, относящиеся к заданиям.
Для каждого чертежа верни:
- task_number — номер задания;
- box_2d — координаты [ymin, xmin, ymax, xmax]
  по шкале от 0 до 1000.

Координаты должны охватывать весь чертёж, но не соседние задания.

Верни только JSON в следующем формате:
{
    "tasks": [
        {
            "task_number": 1,
            "condition": "Текст условия с формулами в LaTeX"
        }
    ],
    "drawings": [
        {
            "task_number": 1,
            "box_2d": [100, 200, 500, 700]
        }
    ]
}
'''


def parse_pdf(pdf_path=PDF_PATH):
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)

    for image_path in IMAGES_DIR.iterdir():
        if image_path.is_file():
            image_path.unlink()

    all_tasks = []
    image_files = {}
    image_counters = {}

    doc = pymupdf.open(pdf_path)

    try:
        print(f'Всего страниц в PDF: {len(doc)}')

        for page_idx, page in enumerate(doc):
            page_num = page_idx + 1
            print(f'\nОбработка страницы {page_num} из {len(doc)}')

            pix = page.get_pixmap(dpi=180)
            page_img = Image.open(io.BytesIO(pix.tobytes('png')))

            img_w, img_h = page_img.size

            try:
                response = generate_with_fallback(
                    contents=[page_img, PROMPT]
                )
                data = json.loads(response.text)

            except Exception as error:
                print(f'Ошибка на странице {page_num}: {error}')
                continue

            for drawing in data.get('drawings', []):
                task_num = drawing.get('task_number')

                try:
                    ymin, xmin, ymax, xmax = drawing['box_2d']
                    ymin = max(0, min(1000, int(ymin)))
                    xmin = max(0, min(1000, int(xmin)))
                    ymax = max(0, min(1000, int(ymax)))
                    xmax = max(0, min(1000, int(xmax)))

                    left = int(xmin * img_w / 1000)
                    top = int(ymin * img_h / 1000)
                    right = int(xmax * img_w / 1000)
                    bottom = int(ymax * img_h / 1000)

                    if right <= left or bottom <= top:
                        print('Пропускаю чертёж с неверными координатами.')
                        continue
                    pad = 6
                    crop_box = (
                        max(0, left - pad),
                        max(0, top - pad),
                        min(img_w, right + pad),
                        min(img_h, bottom + pad),
                    )

                    cropped_img = page_img.crop(crop_box)
                    task_key = str(task_num)
                    image_counters[task_key] = (
                        image_counters.get(task_key, 0) + 1
                    )

                    suffix = image_counters[task_key]
                    img_filename = f'task_{task_key}_{suffix}.png'
                    cropped_img.save(IMAGES_DIR / img_filename)

                    image_files.setdefault(task_key, []).append(img_filename)

                    print(f'  Сохранён чертёж: {img_filename}')

                except (KeyError, TypeError, ValueError) as error:
                    print(f'  Не удалось обработать чертёж: {error}')

            for task in data.get('tasks', []):
                task_num = task.get('task_number')
                condition = task.get('condition', '').strip()

                if task_num is None or not condition:
                    continue

                task_key = str(task_num)
                img_names = image_files.get(task_key, [])

                all_tasks.append({
                    'task_num': task_num,
                    'condition': condition,
                    'image_name': ', '.join(img_names),
                    'solution': '',
                    'answer': '',
                })

                print(f'  Добавлено задание №{task_num}')

    finally:
        doc.close()
    unique_tasks = {}

    for task in all_tasks:
        task_num = task['task_num']

        if task_num not in unique_tasks:
            unique_tasks[task_num] = task
        elif len(task['condition']) > len(
            unique_tasks[task_num]['condition']
        ):
            unique_tasks[task_num] = task

    all_tasks = list(unique_tasks.values())
    all_tasks.sort(key=lambda task: int(task['task_num']))

    print(f'\nВсего собрано заданий: {len(all_tasks)}')

    return all_tasks
