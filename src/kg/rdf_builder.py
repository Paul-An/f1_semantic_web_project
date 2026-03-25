from rdflib import Graph, URIRef
from rdflib.namespace import RDF

from src.kg.uri_utils import build_entity_uri
from src.kg.schema_utils import get_class_uri, get_predicate_uri


def build_rdf_graph(entity_df, relation_df) -> Graph:
    graph = Graph()

    # Add entity type triples
    for _, row in entity_df.iterrows():
        entity_uri = URIRef(build_entity_uri(row["entity_text"]))
        class_uri = get_class_uri(row["entity_type"])

        if class_uri is None:
            continue

        graph.add((entity_uri, RDF.type, URIRef(class_uri)))

    # Add relation triples
    for _, row in relation_df.iterrows():
        subject_uri = URIRef(build_entity_uri(row["subject"]))
        predicate_uri = get_predicate_uri(row["predicate"])
        object_uri = URIRef(build_entity_uri(row["object"]))

        if predicate_uri is None:
            continue

        graph.add((subject_uri, URIRef(predicate_uri), object_uri))

    return graph