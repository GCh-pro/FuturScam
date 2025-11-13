from typing import List, Optional

from app.models import (
    Company,
    DailyRate,
    Conditions,
    Language,
    Skill,
    MissionRequestPending,
)
from app.helpers import (
    parse_datetime,
    safe_dict,
    DEFAULT_MAPPER,
    _get_section,
    _get_top_field,
    to_serializable,
)



class FormatLDG:
    """Formatteur générique des missions LDG.

    Usage :
      formatter = FormatLDG(mapper=custom_mapper)
      mission = formatter.format(json_data)

    Le `mapper` permet d'indiquer comment retrouver les sections principales dans le JSON
    (location, company, budget, publication, role, language, skill) et permet d'adapter
    le parsing si la structure change légèrement. Si aucune mapper n'est fourni, on utilise
    DEFAULT_MAPPER qui correspond au format actuellement attendu.
    """

    def __init__(self, mapper: Optional[dict] = None):
        self.mapper = mapper or DEFAULT_MAPPER

    def format(self, json_data: dict) -> MissionRequestPending:
        # récupérer les sections via le mapper
        loc = _get_section(json_data, self.mapper, "location_section")
        comp_info = _get_section(json_data, self.mapper, "company_section")
        budget_info = _get_section(json_data, self.mapper, "budget_section")
        pub_info = _get_section(json_data, self.mapper, "publication_section")
        role_info = _get_section(json_data, self.mapper, "role_section")
        lang_info = _get_section(json_data, self.mapper, "language_section")
        skill_info = _get_section(json_data, self.mapper, "skill_section")

        # Company
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

        # DailyRate
        currency = safe_dict(budget_info.get("currencyInfo", {})).get("symbol", "")
        max_rate = budget_info.get("maxDailyRate")
        min_rate = budget_info.get("minDailyRate")
        daily_rate = DailyRate(currency, max_rate, min_rate)

        # Conditions
        conditions = Conditions(
            dailyRate=daily_rate,
            fixedMargin=budget_info.get("fixedMargin", 0.0),
            fromAt=None,
            occupation=budget_info.get("occupation", ""),
            startImmediately=budget_info.get("canStartImmediately", False),
            toAt=None,
        )

        # Languages
        languages: List[Language] = []
        for lang_group in lang_info.get("languageGroups", []):
            lg = safe_dict(lang_group)
            level = lg.get("languageLevel", "")
            for lang in lg.get("languages", []):
                languages.append(Language(language=lang, level=level))

        # Skills
        skills: List[Skill] = []
        for skill in skill_info.get("skills", []):
            sk = safe_dict(skill)
            skills.append(Skill(name=sk.get("name", ""), seniority=sk.get("seniority", "")))

        # Dates
        deadlineAt = parse_datetime(pub_info.get("applicationDeadline"))
        publishedAt = parse_datetime(pub_info.get("publishDate"))
        is_active = not pub_info.get("isClosed", True)

        mission_request = MissionRequestPending(
            company=company,
            conditions=conditions,
            contractor=_get_top_field(json_data, self.mapper, "contractingPartyName", ""),
            deadlineAt=deadlineAt,
            isActive=is_active,
            job_desc=_get_top_field(json_data, self.mapper, "description", ""),
            job_id=_get_top_field(json_data, self.mapper, "id", ""),
            job_url=_get_top_field(json_data, self.mapper, "jobUrl", ""),
            languages=languages,
            metadata=None,
            publishedAt=publishedAt,
            remoteOption=loc.get("remoteOption", ""),
            roleTitle=role_info.get("roles", [{}])[0].get("name", ""),
            serviceProvider=_get_top_field(json_data, self.mapper, "managedServiceProviderName", ""),
            skills=skills,
        )

        return mission_request


# wrapper rétrocompatible : garde la même signature pour le reste du code
def parse_mission_request(json_data: dict, mapper: Optional[dict] = None) -> MissionRequestPending:
    formatter = FormatLDG(mapper)
    return formatter.format(json_data)


