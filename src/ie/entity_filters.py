def is_valid_f1_entity(entity_text: str, f1_type: str | None) -> bool:
    if f1_type is None:
        return False

    text = entity_text.strip()

    generic_noise = {
        "Driver",
        "Wins",
        "Formula",
        "Formula One",
        "Formula One’s",
        "Constructors",
        "Races",
        "World Champion",
    }

    if text in generic_noise:
        return False

    if text.endswith("’s") or text.endswith("'s"):
        return False

    if f1_type == "Driver":
        driver_noise = {
            "Spielberg",
            "Adelaide",
            "Melbourne",
        }
        if text in driver_noise:
            return False

    if f1_type == "TeamOrOrganization":
        org_noise = {
            "Alain Prost",
            "Lando Norris",
            "Vettel",
            "Driver",
            "Circuit de Barcelona-Catalunya",
        }
        if text in org_noise:
            return False

    return True