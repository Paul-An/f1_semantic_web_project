from pathlib import Path
import pandas as pd
import numpy as np
from pykeen.pipeline import pipeline
from pykeen.triples import TriplesFactory


def prepare_kge_data(kb_ttl_path: str, output_dir: str = "data/kge") -> dict:
    """
    Prépare les splits train/valid/test depuis le KB.
    """
    from rdflib import Graph, URIRef, Literal
    import random

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    g = Graph()
    g.parse(kb_ttl_path, format="turtle")

    # garde seulement les triples URI
    triples = []
    for s, p, o in g:
        if isinstance(s, URIRef) and isinstance(p, URIRef) and isinstance(o, URIRef):
            triples.append((
                str(s).split("/")[-1],
                str(p).split("/")[-1],
                str(o).split("/")[-1],
            ))

    random.seed(42)
    random.shuffle(triples)

    total     = len(triples)
    train_end = int(total * 0.8)
    valid_end = int(total * 0.9)

    splits = {
        "train": triples[:train_end],
        "valid": triples[train_end:valid_end],
        "test":  triples[valid_end:],
    }

    for name, data in splits.items():
        path = output_path / f"{name}.txt"
        with open(path, "w", encoding="utf-8") as f:
            for s, p, o in data:
                f.write(f"{s}\t{p}\t{o}\n")

    print(f"[kge] Train: {len(splits['train'])} | Valid: {len(splits['valid'])} | Test: {len(splits['test'])}")
    return {k: len(v) for k, v in splits.items()}


def train_model(model_name: str, kge_dir: str = "data/kge", epochs: int = 50) -> dict:
    """
    Entraîne un modèle KGE et retourne les métriques.
    """
    kge_path = Path(kge_dir)

    tf       = TriplesFactory.from_path(kge_path / "train.txt")
    tf_valid = TriplesFactory.from_path(
        kge_path / "valid.txt",
        entity_to_id=tf.entity_to_id,
        relation_to_id=tf.relation_to_id,
    )
    tf_test  = TriplesFactory.from_path(
        kge_path / "test.txt",
        entity_to_id=tf.entity_to_id,
        relation_to_id=tf.relation_to_id,
    )

    result = pipeline(
        training=tf,
        validation=tf_valid,
        testing=tf_test,
        model=model_name,
        model_kwargs={"embedding_dim": 100},
        optimizer="Adam",
        optimizer_kwargs={"lr": 0.01},
        training_kwargs={"num_epochs": epochs, "batch_size": 256},
        evaluation_kwargs={"batch_size": 256},
        random_seed=42,
        device="cpu",
    )

    # sauvegarde le modèle
    result.save_to_directory(str(kge_path / f"{model_name.lower()}_model"))

    # extrait les métriques
    df = result.metric_results.to_df()
    key = df[
        (df["Side"] == "both") &
        (df["Rank_type"] == "realistic") &
        (df["Metric"].isin(["hits_at_1", "hits_at_3", "hits_at_10", "inverse_harmonic_mean_rank"]))
    ]

    metrics = {row["Metric"]: round(row["Value"], 4) for _, row in key.iterrows()}
    metrics["model"] = model_name
    print(f"[kge] {model_name} → MRR={metrics.get('inverse_harmonic_mean_rank')} "
          f"Hits@10={metrics.get('hits_at_10')}")

    return metrics