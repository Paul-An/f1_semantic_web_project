from pathlib import Path
import pandas as pd

from src.ie.preprocessing import normalize_text
from src.ie.ner_utils import load_ner_model, extract_entities
from src.ie.entity_mapping import map_entity_to_f1_type
from src.ie.entity_filters import is_valid_f1_entity
from src.ie.entity_normalization import normalize_entity_name
from src.ie.relation_candidates import extract_relation_candidates
from src.ie.relation_mapping import infer_f1_relation
from src.ie.relation_normalization import normalize_relation_direction


def process_ie_folder(processed_data_dir: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    processed_dir = Path(processed_data_dir)
    txt_files = sorted(processed_dir.glob("seed_page_*.txt"))

    nlp = load_ner_model()

    all_entity_rows = []
    all_relation_rows = []

    for file_path in txt_files:
        with file_path.open("r", encoding="utf-8") as file:
            text = file.read()

        normalized_text = normalize_text(text)

        entities = extract_entities(normalized_text, nlp)
        for entity in entities:
            f1_type = map_entity_to_f1_type(entity["text"], entity["label"])

            if not is_valid_f1_entity(entity["text"], f1_type):
                continue

            normalized_name = normalize_entity_name(entity["text"])

            all_entity_rows.append(
                {
                    "entity_text": normalized_name,
                    "entity_type": f1_type,
                    "source_file": file_path.name,
                }
            )

        relation_candidates = extract_relation_candidates(normalized_text, nlp)

        for candidate in relation_candidates:
            relation_type = infer_f1_relation(
                candidate["sentence"],
                candidate["entity_1"],
                candidate["entity_1_type"],
                candidate["entity_2"],
                candidate["entity_2_type"],
            )

            if relation_type is None:
                continue

            normalized_relation = normalize_relation_direction(
                candidate["entity_1"],
                candidate["entity_1_type"],
                candidate["entity_2"],
                candidate["entity_2_type"],
                relation_type,
            )

            if normalized_relation is None:
                continue

            normalized_relation["source_file"] = file_path.name
            all_relation_rows.append(normalized_relation)

    entity_catalog_df = (
        pd.DataFrame(all_entity_rows)
        .drop_duplicates()
        .sort_values(["entity_type", "entity_text", "source_file"])
        .reset_index(drop=True)
    )

    relation_catalog_df = (
        pd.DataFrame(all_relation_rows)
        .drop_duplicates()
        .sort_values(["predicate", "subject", "object", "source_file"])
        .reset_index(drop=True)
    )

    return entity_catalog_df, relation_catalog_df