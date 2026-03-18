import trafilatura

def extract_main_text(html: str) -> str | None:
    return trafilatura.extract(html)