import html
import re


def clean_latex(text, task_num=None):
    if not text:
        return ''

    text = html.unescape(text)
    text = text.replace('\r\n', '\n').replace('\r', '\n')

    lines = []

    for line in text.splitlines():
        line = line.strip()

        # Убираем строки-разделители таблиц Markdown.
        if re.fullmatch(r'\|[\s:|\-]+\|', line):
            continue

        # Убираем внешние символы таблицы Markdown.
        if line.startswith('|') and line.endswith('|'):
            line = line[1:-1].strip()

        lines.append(line)

    text = '\n'.join(lines)

    # Убираем Markdown-выделение, не затрагивая LaTeX-команды.
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
    text = re.sub(r'(?<!\*)\*([^*\n]+)\*(?!\*)', r'\1', text)

    # Убираем служебные фразы.
    unwanted_phrases = [
        r'Ответ\s*:\s*[_\s]*\.?',
        r'Проверьте,\s*чтобы\s+каждый\s+ответ\s+был\s+записан\s+'
        r'рядом\s+с\s+номером\s+соответствующего\s+задания\.?',
        r'Ответы\s+запишите\s+рядом\s+с\s+номером\s+'
        r'соответствующего\s+задания\.?',
        r'Ответы\s+запишите\s+в\s+виде\s+последовательности\s+цифр\.?',
    ]

    for phrase in unwanted_phrases:
        text = re.sub(
            phrase,
            '',
            text,
            flags=re.IGNORECASE,
        )

    # Убираем номер задания в начале текста, если он там есть.
    if task_num is not None:
        number = re.escape(str(task_num))
        text = re.sub(
            rf'^\s*{number}\s*[.)]\s*',
            '',
            text,
            count=1,
        )

    # Убираем лишние пробелы в начале и конце строк.
    text = '\n'.join(
        line.strip() for line in text.splitlines()
    )

    # Схлопываем повторяющиеся пробелы только вне LaTeX.
    # Содержимое между $...$ оставляем без изменений.
    parts = re.split(r'(\$\$.*?\$\$|\$.*?\$)', text, flags=re.DOTALL)

    for index in range(0, len(parts), 2):
        parts[index] = re.sub(r'[ \t]{2,}', ' ', parts[index])

    text = ''.join(parts)

    # Убираем слишком большие пустые промежутки.
    text = re.sub(r'\n{3,}', '\n\n', text)

    return text.strip()