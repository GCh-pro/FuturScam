import re
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


