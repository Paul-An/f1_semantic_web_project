import re

def normalize_text(text: str) -> str:
    # supprime les lignes de tableau markdown (commencent par |)
    text = re.sub(r'^\|.*\|$', '', text, flags=re.MULTILINE)
    # supprime les lignes vides multiples
    text = re.sub(r'\n{3,}', '\n\n', text)
    # supprime les espaces multiples
    text = re.sub(r'\s+', ' ', text)
    return text.strip()