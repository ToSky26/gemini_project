import pymupdf

from parser.extract_images import extract_images
from parser.extract_tasks import extract_tasks


def parse_pdf(pdf_path):
    with pymupdf.open(pdf_path) as document:
        images_by_page = extract_images(document)
        tasks = extract_tasks(document, images_by_page)

    return tasks
