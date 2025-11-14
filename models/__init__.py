import re
import json
from datetime import datetime
from typing import Any

###############################################################################
# Helpers: lire/écrire/ajouter dans des chemins imbriqués avec dot-notation
###############################################################################

def get_by_path(data: dict, path: str) -> Any:
    """Get a nested value using dot notation and [index]. Returns KeyError/IndexError if absent."""
    parts = re.split(r'\.(?![^\[]*\])', path)
    cur = data
    for p in parts:
        m = re.match(r'(\w+)\[(\d+)\]', p)
        if m:
            key, idx = m.group(1), int(m.group(2))
            cur = cur[key][idx]
        else:
            cur = cur[p]
    return cur

def ensure_path_exists(data: dict, path: str):
    """Ensure intermediate dicts exist for a dot path (for set_by_path)."""
    parts = path.split(".")
    cur = data
    for p in parts[:-1]:
        if p not in cur or not isinstance(cur[p], dict):
            cur[p] = {}
        cur = cur[p]
    return cur

def set_by_path(data: dict, path: str, value: Any):
    """Set a nested value using dot notation. Creates intermediate dicts as needed."""
    cur = ensure_path_exists(data, path)
    last = path.split(".")[-1]
    cur[last] = value

def append_to_list_by_path(data: dict, path: str, value: Any):
    """
    Append a value to a list at `path`. Creates list and intermediate dicts as needed.
    path is dot notation to the list (e.g. 'skills' or 'company.skills').
    """
    parts = path.split(".")
    cur = data
    for p in parts[:-1]:
        if p not in cur or not isinstance(cur[p], dict):
            cur[p] = {}
        cur = cur[p]
    last = parts[-1]
    if last not in cur or not isinstance(cur[last], list):
        cur[last] = []
    cur[last].append(value)

###############################################################################
# Mapping schema (scalars) - garder simple pour champs non-listes
###############################################################################

MAPPING = {
    # company
    "locationInfo.mainLocation.city": "company.city",
    "companyInfo.companyName": "company.name",
    "locationInfo.mainLocation.country": "company.country",
    "locationInfo.mainLocation.street": "company.street",
    "locationInfo.mainLocation.zipCode": "company.zipcode",
    "locationInfo.mainLocation.region": "company.region",

    # conditions
    "budgetInfo.currencyInfo.symbol": "conditions.dailyRate.currency",
    "budgetInfo.minDailyRate": "conditions.dailyRate.min",
    "budgetInfo.maxDailyRate": "conditions.dailyRate.max",
    "budgetInfo.fixedMargin": "conditions.fixedMargin",
    "budgetInfo.startDate": "conditions.fromAt",
    "budgetInfo.endDate": "conditions.toAt",
    "budgetInfo.canStartImmediately": "conditions.startImmediately",
    "budgetInfo.occupation": "conditions.occupation",

    # top-level
    "contractingPartyName": "contractor",
    "publicationInfo.applicationDeadline": "deadlineAt",
    "publicationInfo.publishDate": "publishedAt",
    "jobUrl": "job_url",
    "id": "job_id",
    "description": "job_desc",
    "roleInfo.roles[0].name": "roleTitle",
    "contractingPartyName": "serviceProvider",
    "publicationInfo.isClosed": "isActive",
}

###############################################################################
# LIST_MAPPINGS: déclarer ici comment convertir une liste source -> liste dest
# clé: chemin vers la liste dans source
# valeur: tuple(dest_list_path, item_field_map, optional_transform_fn)
# item_field_map: mapping champ source (clé dans item) -> champ dest (clé dans dest item)
# optional_transform_fn(item, mapped_item) -> can modify mapped_item (useful pour formater)
###############################################################################

def identity_transform(item, mapped_item):
    return mapped_item

LIST_MAPPINGS = {
    # skills: transform chaque élément {'name':..., 'seniority':...} -> same structure in dest 'skills'
    "skillInfo.skills": ("skills", {"name": "name", "seniority": "seniority"}, identity_transform),

    # languages: on doit aplatir les languageGroups vers une liste de {language, level}
    # ici on indique qu'on prendra chaque groupe.languages (liste) et on copiera 'languageLevel' sur chaque entrée correspondante
    # la transform_fn ci-dessous gère la logique
    "languageInfo.languageGroups": (
        "languages",
        # mapping par défaut (sera traité dans transform)
        {},
        lambda item, mapped_item: mapped_item  # placeholder, traitement spécial plus bas
    ),
}

###############################################################################
# Mapper engine
###############################################################################

def map_json(source: dict, mapping: dict, list_mappings: dict) -> dict:
    result = {}

    # 1) scalars/simple mappings
    for src_path, dst_path in mapping.items():
        try:
            value = get_by_path(source, src_path)
            # si on mappe isClosed -> isActive (bool invert), traitement possible ici
            # Si besoin d'adaptations, on peut ajouter des règles spécifiques.
            set_by_path(result, dst_path, value)
        except Exception:
            # champ absent -> on ignore (ou log)
            continue

    # 2) list mappings dynamiques
    for src_list_path, (dst_list_path, item_map, transform_fn) in list_mappings.items():
        try:
            src_list = get_by_path(source, src_list_path)
            # src_list peut être une liste d'items, ou pour languageGroups : une liste de groupes contenant 'languages' sub-lists
            if not isinstance(src_list, list):
                continue

            # cas spécial: language groups -> on veut une liste plate de {language, level}
            if src_list_path == "languageInfo.languageGroups":
                # parcourir tous les groupes
                for group in src_list:
                    languages = group.get("languages", [])
                    level = group.get("languageLevel") or group.get("languageLevelLabel") or None
                    for lang in languages:
                        # chaque 'lang' peut être string ou dict
                        if isinstance(lang, dict):
                            lang_name = lang.get("language") or lang.get("name") or lang
                        else:
                            lang_name = lang
                        mapped_item = {"language": lang_name, "level": level}
                        append_to_list_by_path(result, dst_list_path, mapped_item)
                continue

            # cas général: src_list est liste d'objets simples (skills)
            for item in src_list:
                mapped_item = {}
                # copier les champs selon item_map
                for src_key, dst_key in item_map.items():
                    # si src_key est présent dans item
                    if isinstance(item, dict) and src_key in item:
                        mapped_item[dst_key] = item[src_key]
                # appel du transform_fn pour modifications éventuelles
                mapped_item = transform_fn(item, mapped_item) or mapped_item
                append_to_list_by_path(result, dst_list_path, mapped_item)

        except Exception:
            # si la liste n'existe pas ou autre erreur, on skip
            continue

    return result

###############################################################################
# Petit helper pour tests / chargement
###############################################################################

def load_and_map(filename: str) -> dict:
    with open(filename, "r", encoding="utf-8") as f:
        raw = json.load(f)
    return map_json(raw, MAPPING, LIST_MAPPINGS)

###############################################################################
# Demo
###############################################################################

if __name__ == "__main__":
    # exemple: adapte le nom du fichier
    src_file = "jobpost_JobPostModelToSupplierV1_50497.json"
    mapped = load_and_map(src_file)
    print(json.dumps(mapped, ensure_ascii=False, indent=2))
