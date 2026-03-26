import re
import requests
from rdflib import Graph

OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "gemma2:2b"


def ask_llm(prompt: str) -> str:
    """Envoie un prompt à Ollama et retourne la réponse."""
    response = requests.post(OLLAMA_URL, json={
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
    }, timeout=60)
    return response.json().get("response", "")


def load_graph(ttl_path: str) -> Graph:
    """Charge le KB RDF depuis un fichier Turtle."""
    g = Graph()
    g.parse(ttl_path, format="turtle")
    print(f"[rag] KB chargé : {len(g)} triples")
    return g


def build_schema_summary(g: Graph) -> str:
    """
    Construit un résumé du schéma du KB pour le prompt LLM.
    Inclut les préfixes, classes et prédicats disponibles.
    """
    # préfixes
    prefixes = """PREFIX f1:     <http://example.org/f1/ontology/>
    PREFIX entity: <http://example.org/f1/entity/>
    PREFIX wd:     <http://www.wikidata.org/entity/>
    PREFIX wdt:    <http://www.wikidata.org/prop/direct/>
    PREFIX rdf:    <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    PREFIX rdfs:   <http://www.w3.org/2000/01/rdf-schema#>
    PREFIX owl:    <http://www.w3.org/2002/07/owl#>"""

    # classes
    classes_query = """
    SELECT DISTINCT ?cls WHERE {
        ?s rdf:type ?cls .
        FILTER(STRSTARTS(STR(?cls), "http://example.org/f1/ontology/"))
    } LIMIT 20
    """
    classes = [str(r.cls) for r in g.query(classes_query)]

    # prédicats
    preds_query = """
    SELECT DISTINCT ?p WHERE {
        ?s ?p ?o .
        FILTER(STRSTARTS(STR(?p), "http://example.org/f1/ontology/"))
    } LIMIT 20
    """
    preds = [str(r.p) for r in g.query(preds_query)]

    # exemples de triples
    sample_query = """
    SELECT ?s ?p ?o WHERE {
        ?s ?p ?o .
        FILTER(STRSTARTS(STR(?p), "http://example.org/f1/ontology/"))
    } LIMIT 10
    """
    samples = [
        f"  {str(r.s).split('/')[-1]} {str(r.p).split('/')[-1]} {str(r.o).split('/')[-1]}"
        for r in g.query(sample_query)
    ]

    summary = f"""{prefixes}

# Classes disponibles
{chr(10).join(f'- {c}' for c in classes)}

# Prédicats disponibles
{chr(10).join(f'- {p}' for p in preds)}

# Exemples de triples
{chr(10).join(samples)}
"""
    return summary


def generate_sparql(question: str, schema: str) -> str:
    prompt = f"""You are a SPARQL expert. Generate a valid SPARQL SELECT query.

STRICT RULES:
- ALWAYS start with these exact PREFIX declarations:
  PREFIX f1: <http://example.org/f1/ontology/>
  PREFIX entity: <http://example.org/f1/entity/>
- Use ONLY f1: and entity: prefixes, never wdt: or wd:
- Available predicates: f1:wonGrandPrix, f1:isPartOfSeason, f1:wonConstructorsChampionshipIn
- Available classes: f1:Driver, f1:GrandPrix, f1:Season, f1:Team
- Entity names use underscores: entity:Lewis_Hamilton, entity:Monaco_Grand_Prix, entity:1958
- Triple pattern is always: subject predicate object
- Return ONLY the SPARQL query in a ```sparql code block, nothing else

EXAMPLE 1 - Driver won Grand Prix:
Q: Which Grand Prix did Ayrton Senna win?
```sparql
PREFIX f1: <http://example.org/f1/ontology/>
PREFIX entity: <http://example.org/f1/entity/>
SELECT ?gp WHERE {{
    entity:Ayrton_Senna f1:wonGrandPrix ?gp .
}}
```

EXAMPLE 2 - Grand Prix part of season:
Q: Which season is the Monaco Grand Prix part of?
```sparql
PREFIX f1: <http://example.org/f1/ontology/>
PREFIX entity: <http://example.org/f1/entity/>
SELECT ?season WHERE {{
    entity:Monaco_Grand_Prix f1:isPartOfSeason ?season .
}}
```

EXAMPLE 3 - Team won Constructors Championship:
Q: Which team won the Constructors Championship in 2007?
```sparql
PREFIX f1: <http://example.org/f1/ontology/>
PREFIX entity: <http://example.org/f1/entity/>
SELECT ?team WHERE {{
    ?team f1:wonConstructorsChampionshipIn entity:2007 .
}}
```

EXAMPLE 4 - All championships won by a team:
Q: Which seasons did Ferrari win the Constructors Championship?
```sparql
PREFIX f1: <http://example.org/f1/ontology/>
PREFIX entity: <http://example.org/f1/entity/>
SELECT ?season WHERE {{
    entity:Ferrari f1:wonConstructorsChampionshipIn ?season .
}}
```

QUESTION: {question}
"""
    raw = ask_llm(prompt)
    return _extract_sparql(raw)


def _extract_sparql(text: str) -> str:
    """Extrait la requête SPARQL d'une réponse LLM."""
    match = re.search(r"```sparql\s*(.*?)```", text, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()
    # fallback : cherche SELECT directement
    match = re.search(r"(SELECT.*)", text, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return text.strip()


def run_sparql(g: Graph, query: str) -> tuple[list, list]:
    """Exécute une requête SPARQL sur le KB."""
    results = g.query(query)
    vars_ = [str(v) for v in results.vars]
    rows  = [tuple(str(cell) for cell in row) for row in results]
    return vars_, rows


def repair_sparql(question: str, schema: str, bad_query: str, error: str) -> str:
    """Demande au LLM de corriger une requête SPARQL invalide."""
    prompt = f"""The following SPARQL query failed. Fix it.

SCHEMA:
{schema}

QUESTION: {question}

BAD QUERY:
{bad_query}

ERROR:
{error}

Return ONLY the corrected SPARQL in a ```sparql code block.
"""
    raw = ask_llm(prompt)
    return _extract_sparql(raw)


def answer_with_rag(g: Graph, schema: str, question: str) -> dict:
    """
    Pipeline RAG complet :
    1. Génère SPARQL depuis la question
    2. Exécute sur le KB
    3. Self-repair si erreur
    """
    sparql = generate_sparql(question, schema)

    try:
        vars_, rows = run_sparql(g, sparql)
        return {
            "question": question,
            "sparql":   sparql,
            "vars":     vars_,
            "rows":     rows,
            "repaired": False,
            "error":    None,
        }
    except Exception as e:
        # self-repair
        repaired = repair_sparql(question, schema, sparql, str(e))
        try:
            vars_, rows = run_sparql(g, repaired)
            return {
                "question": question,
                "sparql":   repaired,
                "vars":     vars_,
                "rows":     rows,
                "repaired": True,
                "error":    None,
            }
        except Exception as e2:
            return {
                "question": question,
                "sparql":   repaired,
                "vars":     [],
                "rows":     [],
                "repaired": True,
                "error":    str(e2),
            }


def answer_baseline(question: str) -> str:
    """Répond directement sans RAG — pour comparaison."""
    return ask_llm(f"Answer this question about Formula 1: {question}")


def pretty_print(result: dict) -> None:
    """Affiche le résultat d'une requête RAG."""
    print(f"\nQuestion : {result['question']}")
    print(f"Repaired : {result['repaired']}")
    if result["error"]:
        print(f"Error    : {result['error']}")
    print(f"\nSPARQL:\n{result['sparql']}")
    if result["rows"]:
        print(f"\nRésultats ({len(result['rows'])} lignes):")
        print(" | ".join(result["vars"]))
        for row in result["rows"][:10]:
            print(" | ".join(row))
    else:
        print("\nAucun résultat.")