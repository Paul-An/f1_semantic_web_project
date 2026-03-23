RELATION_SIGNATURES = {
    "wonConstructorsChampionshipIn": ("Team", "Season"),
    "isPartOfSeason": ("GrandPrix", "Season"),
    "wonGrandPrix": ("Driver", "GrandPrix"),
}


def normalize_relation_direction(
    entity_1: str,
    entity_1_type: str,
    entity_2: str,
    entity_2_type: str,
    relation_type: str,
) -> dict | None:
    expected_signature = RELATION_SIGNATURES.get(relation_type)

    if expected_signature is None:
        return None

    expected_subject_type, expected_object_type = expected_signature

    if (entity_1_type, entity_2_type) == expected_signature:
        subject, subject_type = entity_1, entity_1_type
        obj, obj_type = entity_2, entity_2_type

    elif (entity_2_type, entity_1_type) == expected_signature:
        subject, subject_type = entity_2, entity_2_type
        obj, obj_type = entity_1, entity_1_type

    else:
        return None

    return {
        "subject": subject,
        "subject_type": subject_type,
        "predicate": relation_type,
        "object": obj,
        "object_type": obj_type,
    }