import os
import json
import json
from datetime import datetime
from typing import List, Optional

# Classes Python correspondant aux entités UML
import json
from datetime import datetime
from typing import Optional, List

# ----------------- Classes -----------------

class Company:
    def __init__(self, city: str, contact: Optional[str], country: str, name: str, number: Optional[int],
                 region: str, street: str, zipcode: int):
        self.city = city
        self.contact = contact
        self.country = country
        self.name = name
        self.number = number
        self.region = region
        self.street = street
        self.zipcode = zipcode

class DailyRate:
    def __init__(self, currency: str, max_rate: Optional[float], min_rate: Optional[float]):
        self.currency = currency
        self.max = max_rate
        self.min = min_rate

class Conditions:
    def __init__(self, dailyRate: DailyRate, fixedMargin: float, fromAt: Optional[datetime],
                 occupation: str, startImmediately: bool, toAt: Optional[datetime]):
        self.dailyRate = dailyRate
        self.fixedMargin = fixedMargin
        self.fromAt = fromAt
        self.occupation = occupation
        self.startImmediately = startImmediately
        self.toAt = toAt

class Language:
    def __init__(self, language: str, level: str):
        self.language = language
        self.level = level

class Skill:
    def __init__(self, name: str, seniority: str):
        self.name = name
        self.seniority = seniority

class MissionRequestPending:
    def __init__(self, company: Company, conditions: Conditions, contractor: str, deadlineAt: datetime,
                 isActive: bool, job_desc: str, job_id: str, job_url: str,
                 languages: List[Language], metadata: Optional[str], publishedAt: datetime,
                 remoteOption: str, roleTitle: str, serviceProvider: str, skills: List[Skill]):
        self.company = company
        self.conditions = conditions
        self.contractor = contractor
        self.deadlineAt = deadlineAt
        self.isActive = isActive
        self.job_desc = job_desc
        self.job_id = job_id
        self.job_url = job_url
        self.languages = languages
        self.metadata = metadata
        self.publishedAt = publishedAt
        self.remoteOption = remoteOption
        self.roleTitle = roleTitle
        self.serviceProvider = serviceProvider
        self.skills = skills

# ----------------- Fonctions utilitaires -----------------

def parse_datetime(dt_str: Optional[str]) -> Optional[datetime]:
    if dt_str is None:
        return None
    try:
        return datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
    except Exception:
        return None

def safe_dict(obj):
    """Convertit une chaîne JSON en dict si nécessaire."""
    if isinstance(obj, str):
        try:
            return json.loads(obj)
        except json.JSONDecodeError:
            return {}
    elif isinstance(obj, dict):
        return obj
    return {}

# ----------------- Fonction principale -----------------

def parse_mission_request(json_data: dict) -> MissionRequestPending:
    loc = safe_dict(json_data.get("locationInfo", {})).get("mainLocation", {})
    comp_info = safe_dict(json_data.get("companyInfo", {}))
    budget_info = safe_dict(json_data.get("budgetInfo", {}))
    pub_info = safe_dict(json_data.get("publicationInfo", {}))
    role_info = safe_dict(json_data.get("roleInfo", {}))
    lang_info = safe_dict(json_data.get("languageInfo", {}))
    skill_info = safe_dict(json_data.get("skillInfo", {}))

    # ----------------- Company -----------------
    company = Company(
        city=loc.get("city", ""),
        contact=None,
        country=loc.get("country", ""),
        name=comp_info.get("companyName", ""),
        number=None,
        region=loc.get("region", ""),
        street=loc.get("street", ""),
        zipcode=int(loc.get("zipCode", 0)) if loc.get("zipCode") else 0,
    )

    # ----------------- DailyRate -----------------
    currency = safe_dict(budget_info.get("currencyInfo", {})).get("symbol", "")
    max_rate = budget_info.get("maxDailyRate")
    min_rate = budget_info.get("minDailyRate")
    daily_rate = DailyRate(currency, max_rate, min_rate)

    # ----------------- Conditions -----------------
    conditions = Conditions(
        dailyRate=daily_rate,
        fixedMargin=budget_info.get("fixedMargin", 0.0),
        fromAt=None,
        occupation=budget_info.get("occupation", ""),
        startImmediately=budget_info.get("canStartImmediately", False),
        toAt=None,
    )

    # ----------------- Languages -----------------
    languages = []
    for lang_group in lang_info.get("languageGroups", []):
        lang_group = safe_dict(lang_group)
        level = lang_group.get("languageLevel", "")
        for lang in lang_group.get("languages", []):
            languages.append(Language(language=lang, level=level))

    # ----------------- Skills -----------------
    skills = []
    for skill in skill_info.get("skills", []):
        skill = safe_dict(skill)
        skills.append(Skill(name=skill.get("name", ""), seniority=skill.get("seniority", "")))

    # ----------------- Dates -----------------
    deadlineAt = parse_datetime(pub_info.get("applicationDeadline"))
    publishedAt = parse_datetime(pub_info.get("publishDate"))
    is_active = not pub_info.get("isClosed", True)

    mission_request = MissionRequestPending(
        company=company,
        conditions=conditions,
        contractor=json_data.get("contractingPartyName", ""),
        deadlineAt=deadlineAt,
        isActive=is_active,
        job_desc=json_data.get("description", ""),
        job_id=json_data.get("id", ""),
        job_url=json_data.get("jobUrl", ""),
        languages=languages,
        metadata=None,
        publishedAt=publishedAt,
        remoteOption=loc.get("remoteOption", ""),
        roleTitle=role_info.get("roles", [{}])[0].get("name", ""),
        serviceProvider=json_data.get("managedServiceProviderName", ""),
        skills=skills
    )

    return mission_request



def to_serializable(obj):
    if hasattr(obj, "__dict__"):
        return obj.__dict__  # convertit l'objet en dict
    if isinstance(obj, datetime):
        return obj.isoformat()  # convertit les dates en string ISO
    return str(obj)  # fallback

