from pathlib import Path


def load_seed_urls(file_path: str) -> list[str]:
    path = Path(file_path)

    with path.open("r", encoding="utf-8") as f:
        urls = [line.strip() for line in f if line.strip()]

    return urls