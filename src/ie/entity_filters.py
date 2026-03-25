import re


def is_valid_f1_entity(entity_text: str, f1_type: str | None) -> bool:
    if f1_type is None:
        return False

    text = entity_text.strip()

    # texte vide ou trop court
    if len(text) < 3:
        return False

    # commence par une minuscule → bruit (ex: "tyre wear", "van Monaco")
    if text[0].islower():
        return False

    # mots génériques à exclure
    generic_noise = {
        "Driver", "Wins", "Formula", "Formula One", "Formula One's",
        "Constructors", "Races", "World Champion", "Historic",
        "Time", "Nicola", "Linda", "Nicolas", "Aaron", "Adam",
    }
    if text in generic_noise:
        return False

    # suffixes possessifs
    if text.endswith("'s") or text.endswith("'s"):
        return False

    # deux noms propres collés ex: "RussellKimi" (3+ minuscules suivies d'une majuscule)
    if re.search(r'[a-z]{3,}[A-Z]', text):
        return False

    # chiffres avec +
    if re.search(r'\+\d+', text):
        return False

    if f1_type == "Driver":
        # un driver doit avoir au moins 2 mots
        if len(text.split()) < 2:
            return False

    return True