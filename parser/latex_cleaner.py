import html
import re


def clean_latex(text, task_num=None):
    if not text:
        return ''

    text = html.unescape(text)
    text = text.replace('$', '')
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
    text = text.replace(r'\~', ' ')
    text = re.sub(
        r'Ответ\s*:\s*[_\s]*\.?',
        '', text, flags=re.IGNORECASE
    )
    text = re.sub(
        r'Проверьте,\s*чтобы\s+каждый\s+ответ\s+был\s+записан\s+'
        r'рядом\s+с\s+номером\s+соответствующего\s+задания\.?',
        '', text, flags=re.IGNORECASE
    )
    if task_num is not None:
        number = re.escape(str(task_num))
        text = re.sub(rf'^\s*{number}\s*[.)]\s*', '', text, count=1)
    text = '\n'.join(line.rstrip() for line in text.splitlines())
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


def latex_to_readable(text):
    if not text:
        return ''

    text = html.unescape(text)
    text = text.replace(r'\begin{itemize}', '')
    text = text.replace(r'\end{itemize}', '')
    text = text.replace(r'\item', '\n• ')
    text = text.replace('$', '')
    replacements = {
        r'\%': '%',
        r'\~': ' ',
        '~': ' ',
        r'\,': ' ',
        r'\;': ' ',
        r'\!': '',
        r'\times': '×',
        r'\cdot': '·',
        r'\leq': '≤',
        r'\geq': '≥',
        r'\neq': '≠',
        r'\approx': '≈',
        r'\infty': '∞',
        r'\pi': 'π',
        r'\sqrt': '√',
        r'\rightarrow': '→',
        r'\Rightarrow': '⇒',
    }

    for old, new in replacements.items():
        text = text.replace(old, new)
    text = re.sub(r'\\(?:text|mathrm|mathbf)\{([^{}]*)\}', r'\1', text)
    text = text.replace('{', '').replace('}', '')
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'\n\s*', '\n', text)
    text = re.sub(r'\n{3,}', '\n\n', text)

    return text.strip()
