import zipfile

from constants import EXCEL_PATH, ZIP_PATH, IMAGES_DIR


def create_zip():
    if not EXCEL_PATH.exists():
        raise FileNotFoundError(f'Не найден Excel-файл: {EXCEL_PATH}')

    ZIP_PATH.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(ZIP_PATH, 'w', zipfile.ZIP_DEFLATED) as archive:
        archive.write(EXCEL_PATH, arcname=EXCEL_PATH.name)

        if IMAGES_DIR.exists():
            for image_path in IMAGES_DIR.iterdir():
                if image_path.is_file():
                    archive.write(image_path,
                                  arcname=f'images/{image_path.name}')

    print('Архив создан:', ZIP_PATH)
