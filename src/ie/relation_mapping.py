def infer_f1_relation(
    sentence: str,
    entity_1: str,
    entity_1_type: str,
    entity_2: str,
    entity_2_type: str,
) -> str | None:
    sentence_lower = sentence.lower()

    entity_types = {entity_1_type, entity_2_type}

    if (
        entity_types == {"Team", "Season"}
        and ("constructors" in sentence_lower or "championship" in sentence_lower)
    ):
        return "wonConstructorsChampionshipIn"

    if (
        entity_types == {"Driver", "GrandPrix"}
        and ("won" in sentence_lower or "winner" in sentence_lower)
    ):
        return "wonGrandPrix"

    if entity_types == {"GrandPrix", "Season"}:
        return "isPartOfSeason"

    return None