import time
import requests

WIKIDATA_SEARCH_URL = "https://www.wikidata.org/w/api.php"

HEADERS = {
    "User-Agent": "F1-KG-Project/1.0 (student project; paula@example.com)"
}

F1_KEYWORDS = {
    "Driver":        ["formula one", "formula 1", "f1", "racing driver", "grand prix"],
    "Team":          ["formula one", "formula 1", "f1", "constructor", "racing team"],
    "GrandPrix":     ["formula one", "formula 1", "grand prix"],
    "Season":        ["formula one", "formula 1", "season"],
    "CountryOrPlace": [],
}

# noms alternatifs pour les équipes dont le nom court est ambigu
TEAM_SEARCH_ALIASES = {
    "Ferrari":     "Scuderia Ferrari",
    "Mercedes":    "Mercedes F1 team",
    "Alpine":      "Alpine F1 Team",
    "Audi":        "Audi F1 Team",
    "Cadillac":    "Cadillac F1",
}

CONFIDENCE_THRESHOLD = 0.6


def pick_best_match(entity_text: str, entity_type: str, results: list) -> dict | None:
    scored = []
    keywords = F1_KEYWORDS.get(entity_type, [])

    for result in results:
        label       = result.get("label", "")
        description = result.get("description", "").lower()

        # score label (max 0.6)
        if label.lower() == entity_text.lower():
            label_score = 0.6
        elif label.lower().startswith(entity_text.lower()):
            label_score = 0.4
        else:
            label_score = 0.2

        # score domaine (max 0.4)
        domain_score = 0.4 if any(kw in description for kw in keywords) else 0.0

        score = label_score + domain_score
        scored.append((score, result))

    scored.sort(key=lambda x: x[0], reverse=True)
    best_score, best = scored[0]

    if best_score < CONFIDENCE_THRESHOLD:
        return None

    qid = best.get("id", "")
    return {
        "uri":         f"http://www.wikidata.org/entity/{qid}",
        "qid":         qid,
        "label":       best.get("label", ""),
        "description": best.get("description", ""),
        "confidence":  round(best_score, 2),
    }


def search_wikidata_entity(entity_text: str, entity_type: str) -> dict | None:
    
    # utilise l'alias si disponible, sinon le nom original
    search_text = TEAM_SEARCH_ALIASES.get(entity_text, entity_text) if entity_type == "Team" else entity_text

    params = {
        "action": "wbsearchentities",
        "language": "en",
        "format": "json",
        "limit": 10,
        "search": search_text,  # ← search_text, pas entity_text
    }

    try:
        response = requests.get(
            WIKIDATA_SEARCH_URL, params=params, headers=HEADERS, timeout=10
        )
        response.raise_for_status()
        results = response.json().get("search", [])
    except requests.RequestException as e:
        print(f"[wikidata_linker] Erreur pour '{entity_text}': {e}")
        return None

    if not results:
        return None

    # on passe search_text à pick_best_match pour que le scoring soit cohérent
    return pick_best_match(search_text, entity_type, results)


def link_entities(entity_rows: list[dict], delay: float = 0.3) -> list[dict]:
    results = []

    for row in entity_rows:
        entity_text = row["entity_text"]
        entity_type = row["entity_type"]

        match = search_wikidata_entity(entity_text, entity_type)

        if match:
            results.append({
                "entity_text":          entity_text,
                "entity_type":          entity_type,
                "wikidata_uri":         match["uri"],
                "wikidata_qid":         match["qid"],
                "wikidata_label":       match["label"],
                "wikidata_description": match["description"],
                "confidence":           match["confidence"],
            })
        else:
            results.append({
                "entity_text":          entity_text,
                "entity_type":          entity_type,
                "wikidata_uri":         None,
                "wikidata_qid":         None,
                "wikidata_label":       None,
                "wikidata_description": None,
                "confidence":           0.0,
            })

        time.sleep(delay)

    return results