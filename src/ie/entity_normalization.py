import re

def normalize_entity_name(entity_text: str) -> str:
    text = entity_text.strip()

    text = re.sub(r'[A-Z]{2,3}$', '', text).strip()

    replacements = {
        "the Fédération Internationale de l’Automobile": "FIA",
    }

    if text in replacements:
        return replacements[text]

    return text