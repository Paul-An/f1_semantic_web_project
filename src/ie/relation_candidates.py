from itertools import combinations

from src.ie.entity_filters import is_valid_f1_entity
from src.ie.entity_mapping import map_entity_to_f1_type
from src.ie.entity_normalization import normalize_entity_name


def extract_relation_candidates(text: str, nlp) -> list[dict]:
    doc = nlp(text)
    candidates = []

    for sent in doc.sents:
        sentence_text = sent.text.strip()
        if not sentence_text:
            continue

        sentence_entities = []
        seen = set()

        for ent in sent.ents:
            f1_type = map_entity_to_f1_type(ent.text, ent.label_)
            if not is_valid_f1_entity(ent.text, f1_type):
                continue

            normalized_text = normalize_entity_name(ent.text)
            key = (normalized_text, f1_type)

            if key in seen:
                continue

            seen.add(key)
            sentence_entities.append(
                {
                    "entity_text": normalized_text,
                    "entity_type": f1_type,
                }
            )

        for e1, e2 in combinations(sentence_entities, 2):
            candidates.append(
                {
                    "sentence": sentence_text,
                    "entity_1": e1["entity_text"],
                    "entity_1_type": e1["entity_type"],
                    "entity_2": e2["entity_text"],
                    "entity_2_type": e2["entity_type"],
                }
            )

    return candidates