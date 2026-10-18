import hashlib
import io
import re

from PIL import Image

from constants import IMAGES_DIR


def clear_images_folder():
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    image_extensions = {
        '.png', '.jpg', '.jpeg', '.webp', '.bmp', '.tiff'
    }

    for file_path in IMAGES_DIR.iterdir():
        if file_path.is_file() and file_path.suffix.lower() in image_extensions:
            file_path.unlink()
    print('Старые изображения удалены.')


def fix_image_background(image):
    image = image.convert('RGB')
    pixels = image.load()
    width, height = image.size
    corners = [
        pixels[0, 0],
        pixels[width - 1, 0],
        pixels[0, height - 1],
        pixels[width - 1, height - 1],
    ]
    average_brightness = sum(
        sum(pixel) / 3 for pixel in corners
    ) / len(corners)

    if average_brightness >= 45:
        return image

    for y in range(height):
        for x in range(width):
            red, green, blue = pixels[x, y]

            if max(red, green, blue) < 45:
                pixels[x, y] = (255, 255, 255)
    return image


def find_task_areas(page):
    task_pattern = re.compile(r'^\s*(19|1[0-8]|[1-9])\s*\.')
    headers = []
    for block in page.get_text('dict')['blocks']:
        if 'lines' not in block:
            continue

        for line in block['lines']:
            text = ''.join(
                span['text'] for span in line['spans']
            ).strip()

            match = task_pattern.match(text)

            if match:
                headers.append({
                    'task_num': int(match.group(1)),
                    'x': line['bbox'][0],
                    'y': line['bbox'][1],
                })

    page_width = page.rect.width
    page_height = page.rect.height
    task_areas = []

    for column in ('left', 'right'):
        column_headers = [
            header for header in headers
            if (
                (header['x'] < page_width / 2)
                == (column == 'left')
            )
        ]

        column_headers.sort(key=lambda header: header['y'])

        for index, header in enumerate(column_headers):
            end_y = (
                column_headers[index + 1]['y']
                if index + 1 < len(column_headers)
                else page_height - 25
            )

            task_areas.append({
                'task_num': header['task_num'],
                'column': column,
                'start_y': header['y'],
                'end_y': end_y,
            })

    return task_areas


def find_image_task(bbox, task_areas, page_width):
    x0, y0, x1, y1 = bbox
    center_x = (x0 + x1) / 2
    center_y = (y0 + y1) / 2
    image_column = 'left' if center_x < page_width / 2 else 'right'

    for area in task_areas:
        if (
            area['column'] == image_column
            and area['start_y'] <= center_y < area['end_y']
        ):
            return area['task_num']

    return None


def extract_images(document):
    clear_images_folder()
    images_by_page = {}
    saved_images = {}

    for page_number, page in enumerate(document, start=1):
        images_by_page[page_number] = []
        task_areas = find_task_areas(page)

        for image_info in page.get_image_info(xrefs=True):
            xref = image_info.get('xref', 0)

            if not xref:
                continue

            bbox = tuple(image_info['bbox'])
            task_num = find_image_task(bbox, task_areas, page.rect.width)
            if task_num is None:
                continue

            try:
                image_data = document.extract_image(xref)
                image = Image.open(
                    io.BytesIO(image_data['image'])
                ).convert('RGB')
            except Exception:
                continue

            if image.width < 40 or image.height < 40:
                continue

            image = fix_image_background(image)
            image_hash = hashlib.sha256(image.tobytes()).hexdigest()

            if image_hash in saved_images:
                image_name = saved_images[image_hash]
            else:
                image_name = (
                    f'page_{page_number:02d}_'
                    f'img_{len(saved_images) + 1:03d}.png'
                )

                image.save(IMAGES_DIR / image_name)
                saved_images[image_hash] = image_name

            images_by_page[page_number].append({
                'name': image_name,
                'bbox': bbox,
                'task_num': task_num,
            })
    print('Всего уникальных изображений заданий:', len(saved_images))
    return images_by_page
