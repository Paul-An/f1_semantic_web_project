from pathlib import Path
from owlready2 import get_ontology
from owlready2.rule import Imp
from rdflib import Graph


def load_f1_ontology(ontology_xml_path: str):
    path = str(Path(ontology_xml_path).resolve())
    onto = get_ontology(path).load()
    return onto


def load_individuals_from_kb(onto, kb_ttl_path: str) -> int:
    """
    Charge les individus depuis full_kb.ttl dans l'ontologie OWLReady2.
    Utilise rdflib pour lire le KB puis injecte les individus.
    """
    from rdflib.namespace import RDF

    F1_ONTO  = "http://example.org/f1/ontology/"
    F1_ENTITY = "http://example.org/f1/entity/"

    CLASS_MAP = {
        F1_ONTO + "Driver":    onto.Driver,
        F1_ONTO + "Team":      onto.Team,
        F1_ONTO + "GrandPrix": onto.GrandPrix,
        F1_ONTO + "Season":    onto.Season,
    }

    PROP_MAP = {
        F1_ONTO + "wonGrandPrix":                onto.wonGrandPrix,
        F1_ONTO + "isPartOfSeason":              onto.isPartOfSeason,
        F1_ONTO + "wonConstructorsChampionshipIn": onto.wonConstructorsChampionshipIn,
    }

    g = Graph()
    g.parse(kb_ttl_path, format="turtle")

    individuals = {}
    count = 0

    with onto:
        # crée les individus par type
        for subj, pred, obj in g:
            if str(pred) == str(RDF.type):
                cls = CLASS_MAP.get(str(obj))
                if cls and str(subj).startswith(F1_ENTITY):
                    name = str(subj).split("/")[-1]
                    if name not in individuals:
                        individuals[name] = cls(name)
                        count += 1

        # ajoute les relations
        for subj, pred, obj in g:
            prop = PROP_MAP.get(str(pred))
            if prop:
                subj_name = str(subj).split("/")[-1]
                obj_name  = str(obj).split("/")[-1]
                if subj_name in individuals and obj_name in individuals:
                    ind_subj = individuals[subj_name]
                    ind_obj  = individuals[obj_name]
                    if ind_obj not in getattr(ind_subj, prop.name, []):
                        getattr(ind_subj, prop.name).append(ind_obj)

    return count


def add_competed_in_season_rule(onto) -> None:
    with onto:
        if not onto.competedInSeason:
            class competedInSeason(onto.Driver >> onto.Season):
                pass

        rule = Imp()
        rule.set_as_rule(
            "Driver(?d), wonGrandPrix(?d, ?gp), isPartOfSeason(?gp, ?s)"
            " -> competedInSeason(?d, ?s)",
            namespaces=[onto]
        )


def apply_rules(onto) -> list[dict]:
    inferences = []
    for driver in onto.Driver.instances():
        for gp in driver.wonGrandPrix:
            for season in gp.isPartOfSeason:
                if season not in driver.competedInSeason:
                    driver.competedInSeason.append(season)
                    inferences.append({
                        "driver":     driver.name,
                        "grand_prix": gp.name,
                        "season":     season.name,
                    })
    return inferences


def run_reasoning_pipeline(
    ontology_xml_path: str,
    kb_ttl_path: str,
    output_path: str = "kg_artifacts/f1_ontology_with_rules.xml",
) -> dict:
    print("[reasoning] Chargement de l'ontologie...")
    onto = load_f1_ontology(ontology_xml_path)

    print("[reasoning] Chargement des individus depuis le KB...")
    n = load_individuals_from_kb(onto, kb_ttl_path)
    print(f"[reasoning] {n} individus chargés")

    print("[reasoning] Ajout de la règle SWRL...")
    add_competed_in_season_rule(onto)

    print("[reasoning] Application des règles...")
    inferences = apply_rules(onto)
    print(f"[reasoning] {len(inferences)} nouvelles inférences")

    output = str(Path(output_path).resolve())
    onto.save(file=output, format="rdfxml")
    print(f"[reasoning] Sauvegardé → {output_path}")

    return {
        "total_inferences":  len(inferences),
        "drivers_inferred":  len(set(r["driver"] for r in inferences)),
        "inferences":        inferences[:10],
    }