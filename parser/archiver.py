import zipfile

from constants import EXCEL_PATH, ZIP_PATH, IMAGES_DIR


def create_zip():
    '''Создаёт ZIP-архив.'''
    with zipfile.ZipFile(ZIP_PATH, 'w', zipfile.ZIP_DEFLATED) as archive:
        archive.write(EXCEL_PATH, arcname='tasks.xlsx')

        for image_path in IMAGES_DIR.iterdir():
            if image_path.is_file():
                archive.write(image_path, arcname=f'images/{image_path.name}')
    print('Архив создан:', ZIP_PATH)
