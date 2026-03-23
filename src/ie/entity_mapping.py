def map_entity_to_f1_type(entity_text: str, entity_label: str) -> str | None:
    text = entity_text.strip()

    known_teams = {
        "Mercedes",
        "Ferrari",
        "McLaren",
        "Red Bull Racing",
        "Williams",
        "Aston Martin",
        "Alpine",
        "Haas F1 Team",
        "Audi",
        "Cadillac",
        "Racing Bulls",
    }

    if entity_label == "DATE" and text.isdigit() and len(text) == 4:
        return "Season"

    if "Grand Prix" in text:
        return "GrandPrix"

    if text in known_teams:
        return "Team"

    if entity_label == "PERSON":
        forbidden_person_like = {"Driver", "Formula", "Formula One’s"}
        if text in forbidden_person_like:
            return None
        return "Driver"

    if entity_label == "ORG":
        forbidden_org_like = {
            "Constructors",
            "Constructors’ Championships",
            "World Champion",
            "Races",
            "Grands Prix",
            "the Constructors’ Champion",
        }
        if text in forbidden_org_like:
            return None
        return "TeamOrOrganization"

    if entity_label == "GPE":
        if text == "F1":
            return None
        return "CountryOrPlace"

    return None