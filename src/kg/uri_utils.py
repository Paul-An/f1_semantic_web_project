import re
import unicodedata


BASE_ENTITY_URI = "http://example.org/f1/entity/"


def slugify_entity_name(name: str) -> str:
    cleaned = str(name).strip()

    cleaned = unicodedata.normalize("NFKD", cleaned)
    cleaned = cleaned.encode("ascii", "ignore").decode("ascii")

    cleaned = re.sub(r"[^\w\s-]", "", cleaned)
    cleaned = re.sub(r"\s+", "_", cleaned)

    return cleaned


def build_entity_uri(name: str) -> str:
    slug = slugify_entity_name(name)
    return BASE_ENTITY_URI + slug