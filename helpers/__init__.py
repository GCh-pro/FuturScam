import json
from datetime import datetime
from typing import Any, Dict, Optional
import re 

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


def to_serializable(obj):
    if hasattr(obj, "__dict__"):
        return obj.__dict__  # convertit l'objet en dict
    if isinstance(obj, datetime):
        return obj.isoformat()  # convertit les dates en string ISO
    return str(obj)  # fallback

class Serializable:
    def to_dict(self):
        result = {}
        for key, value in self.__dict__.items():
            if isinstance(value, datetime):
                result[key] = value.isoformat()
            elif hasattr(value, "to_dict"):
                result[key] = value.to_dict()
            elif isinstance(value, list):
                result[key] = [
                    v.to_dict() if hasattr(v, "to_dict") else v
                    for v in value
                ]
            else:
                result[key] = value
        return result