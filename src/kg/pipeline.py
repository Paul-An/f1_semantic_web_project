from pathlib import Path
import pandas as pd
from rdflib import Graph

from src.kg.rdf_builder import build_rdf_graph
from src.kg.wikidata_linker import link_entities
from src.kg.alignment_builder import build_alignment_graph, get_aligned_qids
from src.kg.sparql_expander import expand_one_hop, triples_to_rdf_graph

import time


def build_kg_pipeline(
    entity_csv_path: str,
    relation_csv_path: str,
    output_dir: str = "kg_artifacts",
) -> dict:
    """
    Pipeline complet de construction du KG :
    1. Charge les CSVs IE
    2. Construit le graph RDF initial
    3. Linke les entités à Wikidata
    4. Construit le graph d'alignement
    5. Expand via Wikidata SPARQL
    6. Merge et sauvegarde tout

    Returns:
        dict avec les statistiques du KB
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # 1. Charge les CSVs
    entity_df   = pd.read_csv(entity_csv_path)
    relation_df = pd.read_csv(relation_csv_path)
    print(f"[kg_pipeline] {len(entity_df)} entités, {len(relation_df)} relations")

    # 2. Graph RDF initial
    initial_graph = build_rdf_graph(entity_df, relation_df)
    initial_graph.serialize(output_path / "initial_graph.ttl", format="turtle")
    print(f"[kg_pipeline] Initial graph: {len(initial_graph)} triples")

    # 3. Link entities
    entity_rows = (
        entity_df[["entity_text", "entity_type"]]
        .drop_duplicates()
        .to_dict("records")
    )
    linked = link_entities(entity_rows, delay=0.3)
    pd.DataFrame(linked).to_csv(output_path / "entity_alignment_table.csv", index=False)
    n_linked = sum(1 for r in linked if r.get("wikidata_uri"))
    print(f"[kg_pipeline] {n_linked}/{len(entity_rows)} entités liées à Wikidata")

    # 4. Alignment graph
    alignment_graph = build_alignment_graph(linked)
    alignment_graph.serialize(output_path / "alignment.ttl", format="turtle")
    print(f"[kg_pipeline] Alignment graph: {len(alignment_graph)} triples")

    # 5. Expansion 1-hop
    qids = get_aligned_qids(linked, min_confidence=0.6)
    expansion_graph = Graph()
    print(f"[kg_pipeline] Expansion 1-hop pour {len(qids)} entités...")
    for i, qid in enumerate(qids):
        raw = expand_one_hop(qid, limit=200)
        expansion_graph += triples_to_rdf_graph(raw)
        if (i + 1) % 50 == 0:
            print(f"  {i+1}/{len(qids)} — {len(expansion_graph)} triples")
        time.sleep(1.0)

    expansion_graph.serialize(output_path / "expanded.nt", format="nt")
    print(f"[kg_pipeline] Expansion: {len(expansion_graph)} triples")

    # 6. Merge final
    full_kb = initial_graph + alignment_graph + expansion_graph
    full_kb.serialize(output_path / "full_kb.ttl", format="turtle")

    # 7. Stats
    stats = {
        "initial_triples":  len(initial_graph),
        "aligned_entities": n_linked,
        "expanded_triples": len(expansion_graph),
        "total_triples":    len(full_kb),
        "unique_entities":  len(set(str(s) for s, p, o in full_kb)),
        "unique_predicates": len(set(str(p) for s, p, o in full_kb)),
    }

    stats_text = "\n".join(f"{k}: {v}" for k, v in stats.items())
    (output_path / "kb_stats.txt").write_text(stats_text, encoding="utf-8")
    print(f"[kg_pipeline] KB complète: {stats['total_triples']} triples")

    return stats