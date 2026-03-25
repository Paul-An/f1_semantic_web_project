import requests

HEADERS = {
    "User-Agent": "F1-KG-Project/1.0 (student project; paula@example.com)"
}

def fetch_page(url: str) -> str:
    response = requests.get(url, headers=HEADERS, timeout=15)
    response.raise_for_status()
    return response.text