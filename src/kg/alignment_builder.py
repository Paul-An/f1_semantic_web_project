from rdflib import Graph, URIRef, Literal, Namespace
from rdflib.namespace import OWL, XSD

from src.kg.uri_utils import build_entity_uri
from src.kg.schema_utils import PREDICATE_URIS

# alignement des prédicats locaux avec Wikidata
PREDICATE_ALIGNMENT = {
    "wonConstructorsChampionshipIn": "http://www.wikidata.org/prop/direct/P2522",
    "wonGrandPrix":                  "http://www.wikidata.org/prop/direct/P1346",
    "isPartOfSeason":                "http://www.wikidata.org/prop/direct/P361",
}


def build_alignment_graph(linked_entities: list[dict]) -> Graph:
    graph = Graph()

    # namespaces lisibles dans le Turtle
    graph.bind("owl",      OWL)
    graph.bind("wd",       Namespace("http://www.wikidata.org/entity/"))
    graph.bind("f1entity", Namespace("http://example.org/f1/entity/"))
    graph.bind("f1onto",   Namespace("http://example.org/f1/ontology/"))

    # owl:sameAs pour chaque entité liée
    for row in linked_entities:
        if not row.get("wikidata_uri"):
            continue

        local_uri    = URIRef(build_entity_uri(row["entity_text"]))
        wikidata_uri = URIRef(row["wikidata_uri"])
        confidence   = row.get("confidence", 0.0)

        graph.add((local_uri, OWL.sameAs, wikidata_uri))

        # annotation de confiance
        conf_pred = URIRef("http://example.org/f1/ontology/alignmentConfidence")
        graph.add((local_uri, conf_pred, Literal(confidence, datatype=XSD.decimal)))

    # owl:equivalentProperty pour chaque prédicat
    for local_name, wikidata_prop in PREDICATE_ALIGNMENT.items():
        local_uri = URIRef(PREDICATE_URIS.get(local_name, ""))
        if not local_uri:
            continue
        graph.add((local_uri, OWL.equivalentProperty, URIRef(wikidata_prop)))

    return graph


def get_aligned_qids(linked_entities: list[dict], min_confidence: float = 0.6) -> list[str]:
    """Retourne les QIDs des entités liées avec confiance suffisante."""
    return [
        row["wikidata_qid"]
        for row in linked_entities
        if row.get("wikidata_qid") and row.get("confidence", 0.0) >= min_confidence
    ]