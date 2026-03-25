BASE_ONTOLOGY_URI = "http://example.org/f1/ontology/"


CLASS_URIS = {
    "Driver": BASE_ONTOLOGY_URI + "Driver",
    "Team": BASE_ONTOLOGY_URI + "Team",
    "TeamOrOrganization": BASE_ONTOLOGY_URI + "TeamOrOrganization",
    "GrandPrix": BASE_ONTOLOGY_URI + "GrandPrix",
    "Season": BASE_ONTOLOGY_URI + "Season",
    "CountryOrPlace": BASE_ONTOLOGY_URI + "CountryOrPlace",
}


PREDICATE_URIS = {
    "wonConstructorsChampionshipIn": BASE_ONTOLOGY_URI + "wonConstructorsChampionshipIn",
    "isPartOfSeason": BASE_ONTOLOGY_URI + "isPartOfSeason",
    "wonGrandPrix": BASE_ONTOLOGY_URI + "wonGrandPrix",
}


def get_class_uri(entity_type: str) -> str | None:
    return CLASS_URIS.get(entity_type)


def get_predicate_uri(predicate: str) -> str | None:
    return PREDICATE_URIS.get(predicate)