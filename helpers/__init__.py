import json
from datetime import datetime
from typing import Any, Dict, Optional


def parse_datetime(dt_str: Optional[str]) -> Optional[datetime]:
    if dt_str is None:
        return None
    try:
        return datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
    except Exception:
        return None


def safe_dict(obj: Any) -> Dict:
    """Convertit une chaîne JSON en dict si nécessaire."""
    if isinstance(obj, str):
        try:
            return json.loads(obj)
        except json.JSONDecodeError:
            return {}
    elif isinstance(obj, dict):
        return obj
    return {}


# Mapper par défaut : définit les noms des sections/top-level utilisés dans le JSON d'entrée.
DEFAULT_MAPPER = {
    # pour la location : (top_level_section, sub_section)
    "location_section": ("locationInfo", "mainLocation"),
    "company_section": "companyInfo",
    "budget_section": "budgetInfo",
    "publication_section": "publicationInfo",
    "role_section": "roleInfo",
    "language_section": "languageInfo",
    "skill_section": "skillInfo",
    # noms top-level pour champs directs
    "contractingPartyName": "contractingPartyName",
    "description": "description",
    "id": "id",
    "jobUrl": "jobUrl",
    "managedServiceProviderName": "managedServiceProviderName",
}


def _get_section(data: dict, mapper: dict, section_key: str) -> dict:
    """Récupère la section en tenant compte du mapper.

    Si le mapper pour la section est un tuple/list (top, sub) -> renvoie data[top][sub]
    Sinon, renvoie data[mapped_name]
    """
    mapped = mapper.get(section_key)
    if isinstance(mapped, (list, tuple)) and len(mapped) >= 2:
        top, sub = mapped[0], mapped[1]
        return safe_dict(data.get(top, {})).get(sub, {})
    if isinstance(mapped, str):
        return safe_dict(data.get(mapped, {}))
    return {}


def _get_top_field(data: dict, mapper: dict, field_name: str, default=None):
    mapped = mapper.get(field_name, field_name)
    return data.get(mapped, default)


def to_serializable(obj):
    if hasattr(obj, "__dict__"):
        return obj.__dict__  # convertit l'objet en dict
    if isinstance(obj, datetime):
        return obj.isoformat()  # convertit les dates en string ISO
    return str(obj)  # fallback
