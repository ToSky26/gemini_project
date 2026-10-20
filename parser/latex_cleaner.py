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
        if re.fullmatch(r'\|[\s:|\-]+\|', line):
            continue
        if line.startswith('|') and line.endswith('|'):
            line = line[1:-1].strip()

        lines.append(line)

    text = '\n'.join(lines)
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
    text = re.sub(r'(?<!\*)\*([^*\n]+)\*(?!\*)', r'\1', text)
    unwanted_phrases = [
        r'Ответ\s*:\s*[_\s]*\.?',
        r'Проверьте,\s*чтобы\s+каждый\s+ответ\s+был\s+записан\s+'
        r'рядом\s+с\s+номером\s+соответствующего\s+задания\.?',
    ]

    for phrase in unwanted_phrases:
        text = re.sub(
            phrase,
            '',
            text,
            flags=re.IGNORECASE,
        )
    if task_num is not None:
        number = re.escape(str(task_num))
        text = re.sub(
            rf'^\s*{number}\s*[.)]\s*',
            '',
            text,
            count=1,
        )
    text = '\n'.join(
        line.strip() for line in text.splitlines()
    )
    parts = re.split(r'(\$\$.*?\$\$|\$.*?\$)', text, flags=re.DOTALL)

    for index in range(0, len(parts), 2):
        parts[index] = re.sub(r'[ \t]{2,}', ' ', parts[index])
    text = ''.join(parts)
    text = re.sub(r'\n{3,}', '\n\n', text)

    return text.strip()