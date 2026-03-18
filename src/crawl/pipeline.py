from pathlib import Path

from src.crawl.io_utils import load_seed_urls, save_text
from src.crawl.web_utils import fetch_page
from src.crawl.text_utils import extract_main_text

PROJECT_ROOT = Path(__file__).resolve().parents[2]

def crawl_seed_urls(seed_file_path: str) -> list[dict]:
    seed_path = PROJECT_ROOT / seed_file_path
    urls = load_seed_urls(str(seed_path))
    records = []

    for i, url in enumerate(urls, start=1):
        raw_path = PROJECT_ROOT / "data" / "raw" / f"seed_page_{i}.html"
        processed_path = PROJECT_ROOT / "data" / "processed" / f"seed_page_{i}.txt"

        html = fetch_page(url)
        save_text(html, str(raw_path))

        clean_text = extract_main_text(html)

        if clean_text:
            save_text(clean_text, str(processed_path))
            extraction_status = "ok"
            processed_path_value = str(processed_path)
        else:
            extraction_status = "failed"
            processed_path_value = None

        records.append(
            {
                "page_id": i,
                "url": url,
                "raw_html_path": str(raw_path),
                "processed_text_path": processed_path_value,
                "extraction_status": extraction_status,
            }
        )

    return records

from src.crawl.io_utils import save_records_to_csv


def crawl_seed_urls_and_save_manifest(
    seed_file_path: str,
    manifest_output_path: str,
) -> list[dict]:
    records = crawl_seed_urls(seed_file_path)
    save_records_to_csv(records, manifest_output_path)
    return records