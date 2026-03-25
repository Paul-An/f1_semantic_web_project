import time
import requests
from rdflib import Graph, URIRef, Literal

WIKIDATA_SPARQL_URL = "https://query.wikidata.org/sparql"

HEADERS = {
    "User-Agent": "F1-KG-Project/1.0 (student project; paula@example.com)",
    "Accept": "application/sparql-results+json",
}

# prédicats Wikidata qu'on garde — on filtre le reste pour éviter le bruit
ALLOWED_PREDICATES = {
    "http://www.wikidata.org/prop/direct/P31",   # instance of
    "http://www.wikidata.org/prop/direct/P21",   # sex or gender
    "http://www.wikidata.org/prop/direct/P27",   # country of citizenship
    "http://www.wikidata.org/prop/direct/P569",  # date of birth
    "http://www.wikidata.org/prop/direct/P19",   # place of birth
    "http://www.wikidata.org/prop/direct/P54",   # member of sports team
    "http://www.wikidata.org/prop/direct/P1344", # participant in
    "http://www.wikidata.org/prop/direct/P1346", # winner
    "http://www.wikidata.org/prop/direct/P2522", # victory in sports competition
    "http://www.wikidata.org/prop/direct/P17",   # country
    "http://www.wikidata.org/prop/direct/P361",  # part of
    "http://www.wikidata.org/prop/direct/P580",  # start time
    "http://www.wikidata.org/prop/direct/P582",  # end time
    "http://www.wikidata.org/prop/direct/P159",  # headquarters location
    "http://www.wikidata.org/prop/direct/P571",  # inception
    "http://www.wikidata.org/prop/direct/P276",  # location
    "http://www.wikidata.org/prop/direct/P641",  # sport
    # ajouts pour les Grand Prix
    "http://www.wikidata.org/prop/direct/P585",  # point in time
    "http://www.wikidata.org/prop/direct/P625",  # coordinate location
    "http://www.wikidata.org/prop/direct/P710",  # participant
    "http://www.wikidata.org/prop/direct/P1448", # official name
    "http://www.wikidata.org/prop/direct/P2283", # uses
    "http://www.wikidata.org/prop/direct/P3157", # number of laps
    "http://www.wikidata.org/prop/direct/P3450", # sports discipline competed in
}


def _run_sparql(query: str, retries: int = 3, delay: float = 2.0) -> list[dict]:
    """Execute une requête SPARQL sur Wikidata, retourne les bindings."""
    for attempt in range(retries):
        try:
            response = requests.get(
                WIKIDATA_SPARQL_URL,
                params={"query": query, "format": "json"},
                headers=HEADERS,
                timeout=30,
            )
            response.raise_for_status()
            return response.json().get("results", {}).get("bindings", [])
        except requests.RequestException as e:
            print(f"[sparql_expander] Tentative {attempt + 1} échouée: {e}")
            time.sleep(delay * (attempt + 1))
    return []


def expand_one_hop(qid: str, limit: int = 200) -> list[tuple]:
    query = f"""
    SELECT ?p ?o WHERE {{
      wd:{qid} ?p ?o .
      FILTER(STRSTARTS(STR(?p), "http://www.wikidata.org/prop/direct/"))
    }}
    LIMIT {limit}
    """

    bindings = _run_sparql(query)
    triples = []
    subject_uri = f"http://www.wikidata.org/entity/{qid}"

    for row in bindings:
        pred     = row.get("p", {}).get("value", "")
        obj_info = row.get("o", {})
        obj_val  = obj_info.get("value", "")
        obj_type = obj_info.get("type", "")

        if pred not in ALLOWED_PREDICATES:
            continue

        if obj_type == "uri":
            triples.append((subject_uri, pred, ("uri", obj_val)))
        elif obj_type == "literal":
            lang     = obj_info.get("xml:lang")
            datatype = obj_info.get("datatype")
            triples.append((subject_uri, pred, ("literal", obj_val, lang, datatype)))

    return triples


def expand_f1_season(season_year: str, limit: int = 1000) -> list[tuple]:
    """
    Expansion spécialisée : récupère toutes les courses + résultats
    d'une saison F1 donnée. C'est la requête la plus efficace pour
    grossir rapidement le KB.
    """
    query = f"""
    SELECT ?race ?p ?o WHERE {{
      ?race wdt:P31 wd:Q9102 .
      ?race wdt:P580 ?date .
      FILTER(YEAR(?date) = {season_year})
      ?race ?p ?o .
      FILTER(STRSTARTS(STR(?p), "http://www.wikidata.org/prop/direct/"))
    }}
    LIMIT {limit}
    """

    bindings = _run_sparql(query)
    triples = []

    for row in bindings:
        race     = row.get("race", {}).get("value", "")
        pred     = row.get("p",    {}).get("value", "")
        obj_info = row.get("o",    {})
        obj_val  = obj_info.get("value", "")
        obj_type = obj_info.get("type",  "")

        if not race or pred not in ALLOWED_PREDICATES:
            continue

        if obj_type == "uri":
            triples.append((race, pred, ("uri", obj_val)))
        elif obj_type == "literal":
            lang     = obj_info.get("xml:lang")
            datatype = obj_info.get("datatype")
            triples.append((race, pred, ("literal", obj_val, lang, datatype)))

    return triples


def triples_to_rdf_graph(raw_triples: list[tuple]) -> Graph:
    """Convertit la liste de tuples bruts en rdflib Graph."""
    graph = Graph()

    for triple in raw_triples:
        subj_uri, pred_uri, obj = triple
        subject   = URIRef(subj_uri)
        predicate = URIRef(pred_uri)

        if obj[0] == "uri":
            graph.add((subject, predicate, URIRef(obj[1])))
        elif obj[0] == "literal":
            _, value, lang, datatype = obj
            if lang:
                graph.add((subject, predicate, Literal(value, lang=lang)))
            elif datatype:
                graph.add((subject, predicate, Literal(value, datatype=URIRef(datatype))))
            else:
                graph.add((subject, predicate, Literal(value)))

    return graph


def expand_by_team(team_qid: str, limit: int = 500) -> list[tuple]:
    """
    Expansion 2-hop : récupère tous les drivers d'une équipe
    et leurs propriétés.
    """
    query = f"""
    SELECT ?s ?p ?o WHERE {{
      ?s wdt:P54 wd:{team_qid} .
      ?s ?p ?o .
      FILTER(STRSTARTS(STR(?p), "http://www.wikidata.org/prop/direct/"))
    }}
    LIMIT {limit}
    """

    bindings = _run_sparql(query)
    triples = []

    for row in bindings:
        subj     = row.get("s", {}).get("value", "")
        pred     = row.get("p", {}).get("value", "")
        obj_info = row.get("o", {})
        obj_val  = obj_info.get("value", "")
        obj_type = obj_info.get("type", "")

        if not subj or pred not in ALLOWED_PREDICATES:
            continue

        if obj_type == "uri":
            triples.append((subj, pred, ("uri", obj_val)))
        elif obj_type == "literal":
            lang     = obj_info.get("xml:lang")
            datatype = obj_info.get("datatype")
            triples.append((subj, pred, ("literal", obj_val, lang, datatype)))

    return triples

def expand_all(
    qids: list[str],
    team_qids: list[str] | None = None,
    one_hop_limit: int = 200,
    delay: float = 1.0,
) -> Graph:
    merged = Graph()

    print(f"[sparql_expander] Expansion 1-hop pour {len(qids)} entités...")
    for i, qid in enumerate(qids):
        raw = expand_one_hop(qid, limit=one_hop_limit)
        merged += triples_to_rdf_graph(raw)
        if (i + 1) % 50 == 0:
            print(f"  {i+1}/{len(qids)} entités — {len(merged)} triples")
        time.sleep(delay)

    if team_qids:
        print(f"\n[sparql_expander] Expansion 2-hop par équipe...")
        for qid in team_qids:
            raw = expand_by_team(qid, limit=500)
            merged += triples_to_rdf_graph(raw)
            print(f"  {qid} → {len(raw)} triples (total: {len(merged)})")
            time.sleep(delay)

    print(f"\n[sparql_expander] Terminé. Total: {len(merged)} triples")
    return merged