import spacy


def load_ner_model(model_name: str = "en_core_web_sm"):
    return spacy.load(model_name)


def extract_entities(text: str, nlp) -> list[dict]:
    doc = nlp(text)

    entities = []
    for ent in doc.ents:
        entities.append(
            {
                "text": ent.text,
                "label": ent.label_,
                "start": ent.start_char,
                "end": ent.end_char,
            }
        )

    return entities